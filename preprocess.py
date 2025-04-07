import ROOT
import argparse
import os
import sys

thisdir = os.path.abspath(os.path.dirname(__file__))
topdir = os.path.abspath(os.path.join(thisdir, '../'))
sys.path.append(topdir)

if __name__=='__main__':

    # read arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--inputfiles', required=True, nargs='+', help="Input ROOT files")
    parser.add_argument('-t', '--inputtree', required=True)
    parser.add_argument('-o', '--outputdir', required=True, type=os.path.abspath)
    args = parser.parse_args()

    #input_file = ROOT.TFile.Open(args.inputfiles)
    # Open the input ROOT file
    input_tree = ROOT.TChain(args.inputtree)
    for infile in args.inputfiles:
        input_tree.Add(infile)

    # Create an output file and clone the tree structure
    basename = os.path.basename(args.inputfiles[0]).replace('.root', '')
    output_file = ROOT.TFile(f"{basename}_DsSig.root", "RECREATE")
    output_tree = input_tree.CloneTree(0)  # Empty tree with same structure

    output_file2 = ROOT.TFile("DsBkg.root", "RECREATE")
    output_tree2 = input_tree.CloneTree(0)  # Empty tree with same structure

    output_file3 = ROOT.TFile("DstarSig.root", "RECREATE")
    output_tree3 = input_tree.CloneTree(0)  # Empty tree with same structure

    output_file4 = ROOT.TFile("DstarBkg.root", "RECREATE")
    output_tree4 = input_tree.CloneTree(0)  # Empty tree with same structure

    # Loop over events
    n_entries = input_tree.GetEntries()

    # set output directories
    inputfiles = args.inputfiles
    outputdirs = {}
    for infile in inputfiles:
        basename = os.path.basename(infile).replace('.root', '')
        outputdirs[infile] = os.path.join(args.outputdir, basename)

    for i in range(n_entries):

        if i % 10000 == 0:
            print(f'Processing event {i}/{n_entries}')

        input_tree.GetEntry(i)

        # nDsMeson = getattr(input_tree, "DsMeson_pt")  # Get number of DsMesons
        # Check if any DsMeson is matched
        if input_tree.
            has_match = False
            for j in range(len(input_tree.DsMeson_pt)):  # Loop over DsMeson candidates
                if getattr(input_tree, "DsMeson_hasFastGenmatch")[j]:  # Proper indexing
                    has_match = True
                    break
            if has_match:
                output_tree.Fill()  # Store the event
            else:
                output_tree2.Fill()  # Store the event

            has_DstarMatch = False
            for j in range(len(input_tree.DStarMeson_pt)):  # Loop over DsMeson candidates
                if getattr(input_tree, "DStarMeson_hasFastGenmatch")[j]:  # Proper indexing
                    has_DstarMatch = True
                    break
            if has_DstarMatch:
                output_tree3.Fill()  # Store the event
            else:
                output_tree4.Fill()  # Store the event
        
    '''
    candidates = []
    for event in input_tree:
        candidates.append(event.DsMeson_mass)
        has_match = False
        for j in candidates:
            if input_tree.DsMeson_hasFastGenmatch[j]:  # If any candidate matches
                has_match = True
                break
        if has_match:
            output_tree.Fill()  # Store the event
    '''
    
    # make output directories
    for outdir in outputdirs.values():
        if not os.path.exists(outdir):
            os.makedirs(outdir)


    # Write trees to their respective files
    output_file.cd()
    output_tree.Write()

    output_file2.cd()
    output_tree2.Write()

    output_file3.cd()
    output_tree3.Write()

    output_file4.cd()
    output_tree4.Write()

    # Close the files
    output_file.Close()
    output_file2.Close()
    output_file3.Close()
    output_file4.Close()
   # input_file.Close()

    
