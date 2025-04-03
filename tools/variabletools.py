import os
import sys
import json
import numpy as np


class HistogramVariable(object):

  def __init__( self, name, variable, nbins, xlow, xhigh, 
                axtitle=None, shorttitle=None, unit=None, comments=None,
		        iscategorical=None, xlabels=None,
                bins=None ):
    self.name = name
    self.variable = variable
    self.nbins = int(nbins)
    self.xlow = float(xlow)
    self.xhigh = float(xhigh)
    self.axtitle = axtitle
    if( self.axtitle is not None and self.axtitle=='' ): self.axtitle = None
    self.shorttitle = shorttitle
    if( self.shorttitle is not None and self.shorttitle=='' ): self.shorttitle = None
    self.unit = unit
    if( self.unit is not None and self.unit=='' ): self.unit = None
    self.comments = comments
    if( self.comments is not None and self.comments=='' ): self.comments = None
    self.iscategorical = False
    if iscategorical is not None: self.iscategorical = (iscategorical.lower()=='true')
    self.xlabels = xlabels
    # make bins
    self.bins = None
    if( bins is not None and len(bins)>0 ):
        self.bins = np.array([float(el) for el in bins])
    else:
        self.bins = np.linspace(self.xlow, self.xhigh, num=self.nbins+1, endpoint=True)
    self.check_bins()
    self.ordered_keys = (['name','variable','nbins','xlow','xhigh',
                          'axtitle','shorttitle','unit','comments',
                          'iscategorical','xlabels','bins'])

  def check_bins( self ):
    ### check if the "bins" attribute conflicts with "nbins", "xlow" or "xhigh"
    if self.bins is None: return
    if( self.bins[0]!=self.xlow
        or self.bins[-1]!=self.xhigh
        or len(self.bins)-1!=self.nbins ):
        msg = 'ERROR in HistogramVariable.check_bins:'
        msg += ' found incompatible bin specifiers'
        msg += ' (for variable {}).'.format(self.name)
        raise Exception(msg)

  def __str__( self ):
    res = 'HistogramVariable( '
    res += ', '.join(['{}: {}'.format(key,getattr(self,key)) for key in self.ordered_keys])
    res += ' )'
    return res

  def to_txt( self ):
    ### make a conventional .txt representation (e.g. for reading in c++)
    line_elements = []
    line_elements.append(self.name)
    line_elements.append(self.variable)
    if self.bins is None:
      line_elements.append(str(self.nbins))
      line_elements.append(str(self.xlow))
      line_elements.append(str(self.xhigh))
    else:
      line_elements.append('0')
      for binedge in self.bins:
        line_elements.append(str(binedge))
    line = ' '.join(line_elements)
    return line

  def to_dict( self ):
    ### make a dictionary (e.g. for writing to json)
    vardict = ({ 'name' : self.name,
                 'variable' : self.variable,
                 'nbins': self.nbins,
                 'xlow': self.xlow,
                 'xhigh': self.xhigh })
    if self.axtitle is not None: vardict['axtitle'] = self.axtitle
    if self.shorttitle is not None: vardict['shorttitle'] = self.shorttitle
    if self.unit is not None: vardict['unit'] = self.unit
    if self.comments is not None: vardict['comments'] = self.comments
    if self.iscategorical: vardict['iscategorical'] = 'true'
    if self.xlabels is not None: vardict['xlabels'] = self.xlabels
    if self.bins is not None: vardict['bins'] = self.bins
    return vardict

  @staticmethod
  def fromdict( vardict ):
    ### create a HistogramVariable from a dictionary
    if not isinstance( vardict, dict ):
      raise Exception('ERROR in HistogramVariable.fromdict:'
        +' input object should be a dict,'
        +' but found {}'.format(type(vardict)))
    reqkeys = ['name','variable']
    optkeys = (['axtitle','shorttitle','unit','comments',
                'iscategorical','xlabels',
                'nbins','xlow','xhigh','bins'])
    # check if all required keys are present
    for reqkey in reqkeys:
      if( reqkey not in vardict.keys() ):
        raise Exception('ERROR in HistogramVariable.fromdict:'
          +' dict does not contain required key {};'.format(reqkey)
          +' found {}'.format(vardict))
    # check for unrecognized keys
    for key in vardict.keys():
      if key not in reqkeys+optkeys:
        raise Exception('ERROR: in HistogramVariable.fromdict:'
          +' dict contains the key {}'.format(key)
          +' which is not recognized.')
    # special case for bins
    if 'bins' not in vardict.keys():
      # if "bins" are not specified, need "nbins", "xlow" and "xhigh"
      if( 'nbins' not in vardict.keys()
          or 'xlow' not in vardict.keys()
          or 'xhigh' not in vardict.keys() ):
        raise Exception('ERROR in HistogramVariable.fromdict:'
          +' dict must contain either "bins" or "nbins", "xlow" and "xhigh"')
    else:
      # if it is specified, check consistency
      if 'nbins' not in vardict.keys(): vardict['nbins'] = len(vardict['bins'])-1
      if 'xlow' not in vardict.keys(): vardict['xlow'] = vardict['bins'][0]
      if 'xhigh' not in vardict.keys(): vardict['xhigh'] = vardict['bins'][-1]
      if( float(vardict['bins'][0])!=float(vardict['xlow'])
          or float(vardict['bins'][-1])!=float(vardict['xhigh'])
          or len(vardict['bins'])-1!=int(vardict['nbins']) ):
        raise Exception('ERROR in HistogramVariable.fromdict:'
          +' found incompatible bin specifiers for variable {}'.format(vardict['name']))
    # special case for xlabels: length must match nbins
    if 'xlabels' in vardict.keys():
      nlabels = len(vardict['xlabels'])
      nbins = int(vardict['nbins'])
      if( nlabels!=nbins ):
        raise Exception('ERROR: length of "xlabels" must correspond to "nbins",'
          +' but found {} and {} respectively.'.format(nlabels,nbins))
    # all checks are passed, now make the variable
    return HistogramVariable( vardict['name'], vardict['variable'],
                vardict['nbins'], vardict['xlow'], vardict['xhigh'],
                axtitle=vardict.get('axtitle',None),
                shorttitle=vardict.get('shorttitle',None),
                unit=vardict.get('unit',None),
                comments=vardict.get('comments',None),
                iscategorical=vardict.get('iscategorical',None),
                xlabels=vardict.get('xlabels',None),
                bins=vardict.get('bins',None) )

  def getbinlabels( self, extended=False ):
    ### get bin labels
    binlabels = []
    # initialize list of bin edges
    bins = self.bins
    if self.bins is None:
      bins = np.linspace(self.xlow, self.xhigh,num=self.nbins+1)
    nametag = self.name if self.shorttitle is None else self.shorttitle
    for i in range(self.nbins):
      binlabel = ''
      if( self.iscategorical and self.xlabels is not None ):
        if extended: binlabel = '{} = {}'.format(nametag, self.xlabels[i])
        else: binlabel = self.xlabels[i]
      else:
        if i==0:
          if extended: binlabel = '{} < {}'.format(nametag, bins[1])
          else: binlabel = '<{}'.format(bins[1])
        elif i==self.nbins-1:
          if extended: binlabel = '{} > {}'.format(nametag, bins[-2])
          else: binlabel = '>{}'.format(bins[-2])
        else:
          if extended: binlabel = '{} < {} < {}'.format(bins[i], nametag, bins[i+1])
          else: binlabel = '{} - {}'.format(bins[i], bins[i+1])
      binlabels.append(binlabel)
    return binlabels

  def getbinedgelabels( self ):
    ### get bin edge labels
    # initialize list of bin edges
    bins = self.nbins
    if self.bins is None:
      bins = np.linspace(self.xlow, self.xhigh,num=self.nbins+1)
    return ['{}'.format(binedge) for binedge in binedges]


class DoubleHistogramVariable(object):

  def __init__( self, name, primary, secondary ):
    # primary and secondary should be instances of HistogramVariable
    # note: in the c++ implementation, only explicit bins are supported,
    #       so need to enforce here as well (for now).
    self.name = name
    self.primary = primary
    self.secondary = secondary
    if( self.primary.bins is None or self.secondary.bins is None ):
      msg = 'ERROR in DoubleHistogramVariable.__init__:'
      msg += ' only explicit bins are supported for DoubleHistogramVariable,'
      msg += ' but found None for the bins of at least one of both HistogramVariables.'
      raise Exception(msg)
  
  def __str__( self ):
    res = 'DoubleHistogramVariable( name: {}\n'.format(self.name)
    res += '  {}\n'.format(self.primary)
    res += '  {}\n'.format(self.secondary)
    return res

  def to_txt( self ):
    ### make a conventional .txt representation (e.g. for reading in c++)
    firstline = self.primary.to_txt()
    firstline = self.name + ' ' + firstline.split(' ',1)[1]
    secondline = self.secondary.to_txt()
    secondline = self.name + ' ' + secondline.split(' ',1)[1]
    return '\n'.join([firstline, secondline])

  def to_dict( self ):
    ### make a dictionary (e.g. for writing to json)
    vardict = {}
    vardict['name'] = self.name
    vardict['primary'] = self.primary.to_dict()
    vardict['secondary'] = self.secondary.to_dict()
    return vardict

  @staticmethod
  def fromdict( vardict ):
    ### create a DoubleHistogramVariable from a dictionary
    if not isinstance( vardict, dict ):
      raise Exception('ERROR in DoubleHistogramVariable.fromdict:'
        +' input object should be a dict,'
        +' but found {}'.format(type(vardict)))
    reqkeys = ['name','primary','secondary']
    optkeys = []
    # check if all required keys are present
    for reqkey in reqkeys:
      if( reqkey not in vardict.keys() ):
        raise Exception('ERROR in DoubleHistogramVariable.fromdict:'
          +' dict does not contain required key {};'.format(reqkey)
          +' found {}'.format(vardict))
    # check for unrecognized keys
    for key in vardict.keys():
      if key not in reqkeys+optkeys:
        raise Exception('ERROR: in DoubleHistogramVariable.fromdict:'
          +' dict contains the key {}'.format(key)
          +' which is not recognized.')
    # create individual HistogramVariables
    primary = HistogramVariable.fromdict( vardict['primary'] )
    secondary = HistogramVariable.fromdict( vardict['secondary'] )
    # make the DoubleHistogramVariable
    return DoubleHistogramVariable( vardict['name'], primary, secondary )


def read_variables( jsonfile, mode='auto' ):
  ### read a collection of histogram variables
  # input arguments:
  # - mode: either 'single', 'double', or 'auto'
  # return type: list of HistogramVariables (if mode is single)
  #              or list of DoubleHistogramVariables (if mode is double)
  with open(jsonfile, 'r') as f:
    variables = json.load(f)
  if not isinstance( variables, list ):
    raise Exception('ERROR in variabletools.read_variables:'
      +' input object should be a list,'
      +' but found {}'.format(type(variables)))
  res = []
  for var in variables:
    if mode=='single':
      res.append( HistogramVariable.fromdict(var) )
    elif mode=='double':
      res.append( DoubleHistogramVariable.fromdict(var) )
    elif mode=='auto':
      if 'variable' in var.keys(): v = HistogramVariable.fromdict(var)
      elif 'primary' in var.keys(): v = DoubleHistogramVariable.fromdict(var)
      else:
        raise Exception('ERROR in variabletools.read_variables'
          +' something is wrong; run with mode="single" or mode="double" for more details.')
      res.append(v)
  return res

def write_variables_txt( variables, txtfile ):
  ### write a collection of variables in plain txt format
  # (more useful than json for reading in c++).
  # note: works for both HistogramVariables and DoubleHistogramVariables
  lines = []
  for var in variables:
    lines.append( var.to_txt() )
  with open(txtfile, 'w') as f:
    for line in lines:
      f.write(line+'\n')

def get_variable_lines( variable ):
  ### internal helper function for write_variables_json
  vardict = variable.to_dict()
  ordered_keys = (['name','variable','nbins','xlow','xhigh',
                     'axtitle','shorttitle','unit','iscategorical','xlabels',
                     'comments', 'bins'])
  lines = []
  lines.append('{')
  for key in ordered_keys:
    if key not in vardict: continue
    value = vardict[key]
    # formatting operations on the value
    if( isinstance(value,str) ):
      if( '\\' in value ): value = value.replace('\\','\\\\')
    if( isinstance(value,str) or isinstance(value,float) or isinstance(value,int)):
      value = '"{}"'.format(value)
    if( isinstance(value,list) ):
      value = str(value)
      value = value.replace('\'','"')
    # write the line
    lines.append('  "{}": {},'.format(key,value))
  lines[-1] = lines[-1].rstrip(',')
  lines.append('}')
  return lines

def write_variables_json( variables, jsonfile, builtin=False ):
  ### write a collection of variables to json format
  if builtin:
    # use builtin json.dump
    # easier, but not easily readable
    varlist = []
    for var in variables: varlist.append( var.to_dict() )
    with open(jsonfile, 'w') as f:
      json.dump(varlist, f)
  else:
    # manual parsing
    lines = []
    lines.append('[')
    for variable in variables:
      thislines = []
      if isinstance(variable, HistogramVariable):
        thislines = get_variable_lines(variable)
      if isinstance(variable, DoubleHistogramVariable):
        thislines1 = get_variable_lines(variable.primary)
        thislines2 = get_variable_lines(variable.secondary)
        thislines = []
        thislines.append('{ "name": '+'"{}",'.format(variable.name))
        thislines.append('  "primary":')
        for l in thislines1: thislines.append('  {}'.format(l))
        thislines[-1] += ','
        thislines.append('  "secondary":')
        for l in thislines2: thislines.append('  {}'.format(l))
        thislines.append('}')
      for l in thislines: lines.append(l)
      lines[-1] += ','
    lines[-1] = lines[-1].rstrip(',')
    lines.append(']')
    with open(jsonfile, 'w') as f:
      for line in lines: f.write(line+'\n')
