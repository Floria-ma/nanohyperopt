#########################################
# Plot the loss from a hyperopt process #
#########################################


# imports
import os
import sys
import argparse
import pickle as pkl
import matplotlib as mpl
import matplotlib.pyplot as plt


def plotloss( losses, labellist=None,
                colorlist=None, colorsort=False,
                title=None,
                xlims=None, xaxtitle='Iteration',
                yaxlog=False, yaxtitle='Loss value'):
    ### plot one or multiple arrays of loss values
    fig,ax = plt.subplots()
    dolegend = True
    if labellist is None:
        dolegend = False
        labellist = ['dummy']*len(losses)
    if colorlist is None:
        # get a colormap with the right amount of colors
        colormap = mpl.cm.get_cmap('jet', len(losses))
        colorlist = [mpl.colors.rgb2hex(colormap(i)) for i in range(colormap.N)]
        if colorsort:
            # re-index the losses to sort according to last loss value
            lastloss = [l[-1] for l in losses]
            sorted_inds = [i[0] for i in sorted(enumerate(lastloss), key=lambda x:x[1])]
            losses = [losses[i] for i in sorted_inds]
            # revert losses and colorlist to plot lowest loss last
            losses = losses[::-1]
            colorlist = colorlist[::-1]
    for loss, label, color in zip(losses, labellist, colorlist):
        ax.plot(loss, color=color,
                linewidth=2, label=label)
    if dolegend: ax.legend()
    if yaxlog: ax.set_yscale('log')
    if xlims is not None: ax.set_xlim(xlims)
    if title is not None: ax.set_title(title)
    if xaxtitle is not None: ax.set_xlabel(xaxtitle)
    if yaxtitle is not None: ax.set_ylabel(yaxtitle)
    return (fig,ax)


if __name__=='__main__':

    # read arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--inputfile', required=True, nargs='+')
    parser.add_argument('-o', '--outputfile', required=True)
    parser.add_argument('-s', '--sort', default=False, action='store_true')
    args = parser.parse_args()

    # print arguments
    print('Running with following configuration:')
    for arg in vars(args): print('  - {}: {}'.format(arg,getattr(args,arg)))
    
    # load the losses
    losses = []
    for inputfile in args.inputfile:
        with open(inputfile,'rb') as f:
            trials = pkl.load(f)
        loss = trials.losses()
        if args.sort: loss.sort(reverse=True)
        losses.append( loss )

    # hard coded arguments
    extratext = 'CMS Preliminary\n\n'
    extratext += 'Results for cut optimization\n'
    extratext += 'using hyperopt'
    if args.sort: extratext += '\n(sorted)'
    extratext_coords = (0.05, 0.25)

    # make the figure
    (fig,ax) = plotloss( losses, 
                colorsort=True,
                title=None,
                xlims=None, xaxtitle='Iteration',
                yaxlog=False, yaxtitle='Loss value' )
    ax.text(extratext_coords[0], extratext_coords[1], extratext,
            horizontalalignment='left', verticalalignment='top', transform=ax.transAxes,
            backgroundcolor='white')
    fig.savefig(args.outputfile)
