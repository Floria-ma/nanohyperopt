######################################################
# Get the best configuration from a hyperopt process #
######################################################


# imports
import os
import sys
import argparse
import pickle as pkl


def get_best_indices(trials, nbest=1):
    ### return indices of lowest-loss iterations in a trials object
    # note: the indices are sorted from lower to higher loss value
    losses = trials.losses()
    if nbest>len(losses): nbest = len(losses)
    sorted_indices = sorted(range(len(losses)), key=lambda k: losses[k])
    return sorted_indices[:nbest]

def get_best_info(trials, nbest=1):
    ### return information of lowest-loss iterations in a trials object
    best_info = []
    losses = trials.losses()
    ids = get_best_indices(trials, nbest=nbest)
    for idx in ids:
        this_info = {}
        this_info['loss'] = losses[idx]
        infodict = trials.trials[idx]['result']['extra_info']
        for key,val in infodict.items():
            this_info[key] = val
        this_info['config'] = {}
        for name,val in trials.trials[idx]['misc']['vals'].items():
            this_info['config'][name] = val
        best_info.append(this_info)
    return best_info

 
if __name__=='__main__':

    # read arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--inputfile', required=True, nargs='+')
    parser.add_argument('-n', '--nbest', type=int, default=1)
    args = parser.parse_args()

    # print arguments
    print('Running with following configuration:')
    for arg in vars(args): print('  - {}: {}'.format(arg,getattr(args,arg)))

    # run over input files
    # (can be multiple, e.g. in the case of multiple parallel jobs as cross-check)
    for inputfile in args.inputfile:
        with open(inputfile,'rb') as f:
            trials = pkl.load(f)
        info = get_best_info(trials, nbest = args.nbest)
        for idx in range(len(info)):
            print('--- configuration {} ---'.format(idx))
            print('loss: {}'.format(info[idx]['loss']))
            for key,val in info[idx].items(): 
                if key=='loss': continue   # already printed
                if key=='config': continue # will be printed later
                print('{}: {}'.format(key, val))
            print('config:')
            for name,val in info[idx]['config'].items(): print('  - {}: {}'.format(name,val))
