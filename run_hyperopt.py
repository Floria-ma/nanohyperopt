#####################################
# Run hyperopt for cut optimization #
#####################################


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


def pass_selection( events, cuts ):
    ### get a mask for a particular configuration of cuts
    # input arguments:
    # - events: NanoAOD events array
    # - cuts: dictionary mapping a variable name to a cut value
    mask = np.ones(len(events)).astype(bool)
    for cutname, cutvalue in cuts.items():
        # parse cut name
        ismax = cutname.endswith('_max')
        ismin = cutname.endswith('_min')
        if( not (ismax or ismin) ): 
            raise Exception('ERROR: cut {} is neither min nor max.'.format(cutname))
        varname = cutname[:-4]
        # get the variable value
        # todo: update to other scenarios
        varvalue = None
        if varname=='MET_pt': varvalue = events.MET.pt
        else:
            raise Exception('ERROR: variable {} not recognized.'.format(varname))
        # perform the cut
        if ismax: mask = ((mask) & (varvalue < cutvalue))
        if ismin: mask = ((mask) & (varvalue > cutvalue))
    return mask


def calculate_loss( events, cuts,
                    sig_mask=None,
                    lossfunction='negsoverb',
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
    if lossfunction=='negsoverb':
        if nbkg_pass == 0: loss = 0.
        else: loss = -nsig_pass / nbkg_pass
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
    parser.add_argument('-i', '--inputfile', required=True)
    parser.add_argument('-g', '--gridfile', required=True)
    parser.add_argument('-o', '--outputfile', default=None)
    parser.add_argument('-n', '--niterations', type=int, default=10)
    parser.add_argument('--nentries', type=int, default=-1)
    parser.add_argument('--nstartup', type=int, default=10)
    args = parser.parse_args()

    # print arguments
    print('Running with following configuration:')
    for arg in vars(args): print('  - {}: {}'.format(arg,getattr(args,arg))) 

    # load the events array
    events = NanoEventsFactory.from_root(
      args.inputfile,
      entry_stop=args.nentries if args.nentries>=0 else None,
      schemaclass=NanoAODSchema
    ).events()

    # define signal mask
    # todo: update to something realistic
    sig_mask = (events.MET.pt > 55.)
    
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
