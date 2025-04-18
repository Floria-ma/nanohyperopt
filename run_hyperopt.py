import ROOT
# imports
import sys
import os
import argparse
import numpy as np
import awkward as ak
import pickle as pkl
from coffea.nanoevents import NanoEventsFactory, NanoAODSchema
from hyperopt import hp, fmin, tpe, STATUS_OK, Trials
from functools import partial
import uproot

# local imports
sys.path.append('tools')
from make_input_file import make_input_file

#####################################
# Run hyperopt for cut optimization #
#####################################

def make_input_file(
    sigfiles=[],
    bkgfiles=[],
    nentriesperfile=-1,
    sigvar='isSignal',
):
    issignal = [True] * len(sigfiles) + [False] * len(bkgfiles)
    allevents = []

    for idx, inputfile in enumerate(sigfiles + bkgfiles):
        tree = uproot.open(f"{inputfile}:Events")
        
        # Load all branches, optionally limit number of entries
        events = tree.arrays(entry_stop=nentriesperfile if nentriesperfile >= 0 else None, library="ak")

        # Add signal label to each event
        events = ak.with_field(events, issignal[idx], where=sigvar)

        allevents.append(events)

    # Concatenate all signal and background events
    events = ak.concatenate(allevents)

    return events

def pass_selection( events, cuts ):
    ### get a mask for a particular configuration of cuts
    # input arguments:
    # - events: NanoAOD events array
    # - cuts: dictionary mapping a variable name to a cut value
    #         note: each key in the dict is supposed to be formatted
    #               as <variable name>_<type>, where <type> is either min or max,
    #               and <variable name> can contain underscores for sub-variables,
    #               e.g. MET_pt for MET.pt
    mask = np.ones(len(events)).astype(bool)
    for cutname, cutvalue in cuts.items():
        # parse cut name
        ismax = cutname.endswith('_max')
        ismin = cutname.endswith('_min')
        if( not (ismax or ismin) ): 
            raise Exception('ERROR: cut {} is neither min nor max.'.format(cutname))
        varname = cutname[:-4]
        # parse variable name
       # varnameparts = varname.split('_')
        # get the variable value
        varvalue = events[varname]
        
       # for varnamepart in varnameparts[1:]: varvalue = getattr(varvalue, varnamepart)
        # if the varvalue is an array instead of a single value per event,
        # take minimum or maximum depending on the cut type
        if(varvalue.layout.minmax_depth[0]==1): pass
        elif(varvalue.layout.minmax_depth[0]==2): 
            if ismin: varvalue = ak.min(varvalue, axis=-1)
            if ismax: varvalue = ak.max(varvalue, axis=-1)
        else:
            msg = 'ERROR: shape of value array for variable {} not recognized.'.format(varname)
            raise Exception(msg)
        # perform the cut
        if ismax: mask = ((mask) & (varvalue < cutvalue))
        if ismin: mask = ((mask) & (varvalue > cutvalue))
    return mask


def calculate_loss( events, cuts,
                    sig_mask=None,
                    lossfunction='s/b',
                    iteration=None):
    ### calculate the loss function for a given configuration of cuts

    # print progress
    #print('Now processing iteration {}'.format(iteration[0]))
    iteration[0] += 1

    # do event selection
    sel_mask = pass_selection(events, cuts)

    # calculate number of passing events
    # todo: use sum of relevant weights instead of sum of entries
    nsig_tot = np.sum(sig_mask)
    nsig_pass = np.sum((sig_mask) & (sel_mask))
    nbkg_tot = np.sum(~sig_mask)
    nbkg_pass = np.sum((~sig_mask) & (sel_mask))

    # calculate loss
    if lossfunction=='s/b':
        if nbkg_pass == 0: loss = 0.
        else: loss = -nsig_pass / nbkg_pass
    elif lossfunction=='s/sqrt(b)':
        if nbkg_pass == 0: loss = 0
        else: loss = -nsig_pass / np.sqrt(nbkg_pass)
    elif lossfunction=='s/sqrt(s+b)':
        if( nsig_pass==0 and nbkg_pass==0 ): loss = 0
        else: loss = -nsig_pass / np.sqrt(nsig_pass + nbkg_pass)
    else:
        msg = 'ERROR: loss function {} not recognized.'.format(lossfunction)
        raise Exception(msg)

    # extend with other loss function definitions
    extra_info = {'nsig_tot': nsig_tot,
                  'nsig_pass': nsig_pass,
                  'nbkg_tot': nbkg_tot,
                  'nbkg_pass': nbkg_pass,
                  'lossfunction': lossfunction}
    return {'loss':loss, 'status':STATUS_OK, 'extra_info': extra_info}


if __name__=='__main__':

    # read arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--sigfiles', required=True, nargs='+')
    parser.add_argument('-b', '--bkgfiles', default=[], nargs='+')
    parser.add_argument('-g', '--gridfile', required=True)
    parser.add_argument('-o', '--outputfile', default=None)
    parser.add_argument('-n', '--niterations', type=int, default=10)
    parser.add_argument('-l', '--lossfunction', default='s/b')
    parser.add_argument('--nentriesperfile', type=int, default=-1)
    parser.add_argument('--nstartup', type=int, default=10)
    args = parser.parse_args()

    # print arguments
    print('Running with following configuration:')
    for arg in vars(args): print('  - {}: {}'.format(arg,getattr(args,arg))) 

    # load the input files
    sigvar = 'isSignal'
    events = make_input_file(sigfiles=args.sigfiles,
      bkgfiles=args.bkgfiles,
      nentriesperfile=args.nentriesperfile,
      sigvar=sigvar)

    # define signal mask
    #sig_mask = (events.MET.pt > 55.) # only for testing
    sig_mask = getattr(events, sigvar)

    # do some printouts
    print('Number of events from inut files:')
    print(' - Signal: {}'.format(ak.sum(sig_mask)))
    print(' - Background: {}'.format(ak.sum(~sig_mask)))
    print(' - Total: {}'.format(len(events)))
    
    # get the grid
    with open(args.gridfile,'rb') as f:
        obj = pkl.load(f)
        grid = obj['grid']
        gridstr = obj['description']
    print('Found following grid:')
    print(gridstr)

    # run hyperopt
    trials = Trials()
    iteration = [1]
    best = fmin(
      fn=partial(calculate_loss, events,
                 sig_mask=sig_mask,
                 lossfunction=args.lossfunction,
                 iteration=iteration
      ),
      space=grid,
      algo=partial(tpe.suggest, n_startup_jobs=args.nstartup),
      max_evals=args.niterations,
      trials=trials
    )

    # write search results to output file
    if args.outputfile is not None:
        print('Writing results to {}'.format(args.outputfile))
        with open(args.outputfile,'wb') as f:
            pkl.dump(trials,f)