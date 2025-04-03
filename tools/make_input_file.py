################################################################
# Prepare a merged NanoEventsArray from multiple NanoAOD files #
################################################################


# imports
import os
import sys
import argparse
import awkward as ak
from coffea.nanoevents import NanoEventsFactory, NanoAODSchema


def make_input_file(
    inputfiles=[],
    nentriesperfile=-1,
    sigvar='isSignal'):
    
    # loop over input files
    issignal = [True]*len(sigfiles) + [False]*len(bkgfiles)
    allevents = []
    for idx,inputfile in enumerate(sigfiles + bkgfiles):
        # load the events array
        events = NanoEventsFactory.from_root(
          inputfile,
          entry_stop=nentriesperfile if nentriesperfile>=0 else None,
          schemaclass=NanoAODSchema
        ).events()
        # add signal variable
        events = ak.with_field(events, issignal[idx], where=sigvar)
        allevents.append(events)
    # concatenate all individual arrays
    events = ak.concatenate(allevents)
    return events
