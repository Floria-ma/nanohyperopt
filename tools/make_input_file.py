################################################################
# Prepare a merged NanoEventsArray from multiple NanoAOD files #
################################################################


# imports
import os
import sys
import argparse
import awkward as ak
from coffea.nanoevents import NanoEventsFactory, NanoAODSchema
import uproot


def make_input_file(
    sigfiles=[],
    bkgfiles=[],
    nentriesperfile=-1,
    sigvar='isSignal'):

    # loop over input files
    issignal = [True] * len(sigfiles) + [False] * len(bkgfiles)
    allevents = []
    for idx, inputfile in enumerate(sigfiles + bkgfiles):

        #load the tree
        tree = uproot.open(f"{inputfile}:Events")
        #load all branches, optionally limit number of entries. 
        # Note that now the fields are directly the branches.
        events = tree.arrays(entry_stop=nentriesperfile if nentriesperfile >= 0 else None, library="ak")
        # Add signal label to each event
        events = ak.with_field(events, issignal[idx], where=sigvar)
        allevents.append(events)

    # Concatenate all signal and background events
    events = ak.concatenate(allevents)
    return events