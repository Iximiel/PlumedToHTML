from pygments.lexer import RegexLexer, bygroups, include
from pygments.formatter import Formatter
from pygments.token import *
import json

class PlumedLexer(RegexLexer):
    name = 'plumed'
    aliases = ['plumed']
    filenames = ['*.plmd']

    tokens = {
        'defaults' : [
            # Deals with blank lines
            (r'\s+$', Text),
            # Deals with all comments
            (r'#.*?$', Comment),
            # Deals with incomplete inputs 
            (r'__FILL__', Literal),  
            # Find LABEL=lab
            (r'(LABEL)(=)(\S+\s)', bygroups(Name.Attribute, Text, String)),
            # Find special replica syntax with brackets
            (r'(\w+)(=)(@replicas:)((?s)\{.*?\})', bygroups(Name.Attribute, Text, Name.Constant, Generic)),  
            # Find special replica syntax without brackets
            (r'(\w+)(=)(@replicas:)(\S+\s)', bygroups(Name.Attribute, Text, Name.Constant, Generic)),
            # Find KEYWORD with brackets around value
            (r'(\w+)(=)((?s)\{.*?\})', bygroups(Name.Attribute, Text, Generic)),
            # Find KEYWORD=whatever 
            (r'(\w+)(=)(\S+\s)', bygroups(Name.Attribute, Text, Generic))
         ],
        'root': [
            include('defaults'), 
            # Find label: ACTION
            (r'(\w+)(:\s+)(\S+\s)', bygroups(String, Text, Keyword)),
            # Find ... for start of continuation
            (r'\.\.\.', Text, 'continuation'),
            # Find ACTION at start of line
            (r'^\s*\w+\s',Keyword),
            # Find FLAG anywhere on line
            (r'\w+\s',Name.Attribute),
            # Find any left over white space
            (r'\s+',Text)
        ],
        'continuation' : [
            include('defaults'),
            # Find FLAG which can now be anywhere on line or at start of line in continuation
            (r'\w+\s', Name.Attribute),
            # Find any left over white space 
            (r'\s+', Text),
            # Find ... ACTION as end of continuation
            (r'(\.\.\.\s+)(\S+$)', bygroups(Text, Text), '#pop'),
            # Find ... as end of continuation
            (r'\.\.\.', Text, '#pop')
        ]
    }

class PlumedFormatter(Formatter):
    def __init__(self, **options) :
        Formatter.__init__(self, **options) 
        # Retrieve the dictionary of keywords from the json
        with open(options["keyword_file"]) as f : self.keyword_dict = json.load(f)
        self.divname=options["input_name"]
        self.egname=options["input_name"]

    def format(self, tokensource, outfile):
        action, label, all_labels, keywords = "", "", [], [] 
        outfile.write('<pre style="width=97%;" class="fragment">\n')
        for ttype, value in tokensource :
            # This checks if we are at the start of a new action.  If we are we should be reading a value or an action and the label and action for the previous one should be set
            if len(action)>0 and (ttype==String or ttype==Keyword) :
               if ("output" not in self.keyword_dict[action] or len(label)>0) :  
                  # This outputs information on the values computed in the previous action for the header
                  if "output" in self.keyword_dict[action] : self.writeValuesData( outfile, action, label, keywords, self.keyword_dict[action]["output"] )
                  # Reset everything for the new action
                  action, label, keywords = "", "", []
               # Check that a label has been given to actions that have output
               elif len(label)==0 and ttype==Keyword :
                  if "output" in self.keyword_dict[action] : raise Exception("action " + action + " has output but does not have label")
                  # Reset everything as we are at the start of a new action that does not have any output
                  else : action, label, keywords = "", "", [] 

            if ttype==Text :
               # Non PLUMED stuff
               outfile.write( value )
            elif ttype==Literal :
               # __FILL__ for incomplete values
               outfile.write('<span style="background-color:yellow">__FILL__</span>')
            elif ttype==Generic:
               # whatever in KEYWORD=whatever (notice special treatment because we want to find labels so we can show paths)
               inputs, nocomma = value.split(","), True
               for inp in inputs : 
                   islab, inpt = False, inp.strip()
                   for lab in all_labels : 
                       if inpt.split('.')[0]==lab : 
                          islab=True
                          break
                   if not nocomma : outfile.write(',')
                   if islab : outfile.write('<b name="' + self.egname + inpt.split('.')[0] + '">' + inp + '</b>')
                   else : outfile.write( inp )
                   nocomma = False 
            elif ttype==String :
               # Labels of actions
               label = value.strip() 
               all_labels.append( label )
               outfile.write('<b name="' + self.egname + label + '" onclick=\'showPath("' + self.divname + '","' + self.egname + label + '")\'>' + value + '</b>')
            elif ttype==Comment :
               # Comments
               outfile.write('<span style="color:blue">' + value + '</span>' )
            elif ttype==Name.Attribute :
               # KEYWORD in KEYWORD=whatever and FLAGS
               keywords.append( value.strip() )
               outfile.write('<div class="tooltip">' + value + '<div class="right">' + self.keyword_dict[action][value.strip()].split('.')[0] + '<i></i></div></div>')
            elif ttype==Name.Constant :
               # @replicas in special replica syntax
               outfile.write('<div class="tooltip">' + value + '<div class="right">This flag is used in simulations with multiple replicas. The first replica uses the first value provided.  The second uses the second and so on.<i></i></div></div>')
            elif ttype==Keyword :
               # Name of action
               action = value.strip()
               outfile.write('<a href="' + self.keyword_dict[action]["hyperlink"] + '" style="color:green">' + value + '</a>')
          
        # Check if there is stuff to output for the last action in the file
        if "output" in self.keyword_dict[action] :
           if len(label)==0 : raise Exception("action " + action + " has output but does not have label") 
           self.writeValuesData( outfile, action, label, keywords, self.keyword_dict[action]["output"] )
        outfile.write('</pre></div>')

    def writeValuesData( self, outfile, action, label, keywords, outdict ) :
        # Some header stuff 
        outfile.write('<span style="display:none;" id="' + self.egname + label + r'">')
        outfile.write('The ' + action + ' action with label <b>' + label + '</b>')
        # Check for components
        found_flags = False
        for key, value in outdict.items() :
            for flag in keywords :
                if flag==value["flag"] or value["flag"]=="default" : found_flags=True
        # Output string for value
        if not found_flags and "value" in outdict : 
            outfile.write(' calculates ' + outdict["value"]["description"] )
        # Output table containing descriptions of all components
        else :
            outfile.write(' calculates the following quantities:')
            outfile.write('<table  align="center" frame="void" width="95%" cellpadding="5%">')
            outfile.write('<tr><td width="5%"><b> Quantity </b>  </td><td><b> Description </b> </td></tr>')    
            for key, value in outdict.items() :
                present = False 
                for flag in keywords : 
                    if flag==value["flag"] : present=True
                if present or value["flag"]=="default" : outfile.write('<tr><td width="5%">' + label + "." + key + '</td><td>' + value["description"] + '</td></tr>')
            outfile.write('</table>')

        outfile.write('</span>')
 
