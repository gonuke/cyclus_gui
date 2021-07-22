#import xmltodict
import copy
import numpy as np
import shutil
import json
import re
import os
import subprocess
import pprint
import sys
here = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(here, os.pardir, os.pardir, 'wasppy'))
from xml2obj import xml2obj


# PPHW: defining some colors to be used later for syntax highlighting
class highlighter:
    def __init__(self):
        self.rgb_dict = {'black': [0,0,0],
                         'white': [255, 255, 255],
                         'red': [255, 0, 0],
                         'lime': [0, 255, 0],
                         'blue': [0, 0, 255],
                         'yellow': [255, 255, 0],
                         'cyan': [0, 255, 255],
                         'magenta': [255, 0, 255],
                         'silver': [192, 192, 192]}
        self.highlight_str = self.make_basic_son()

    
# PPHW: shortcut to help define rules
    def highlight_maker(self, name, word, color='blue'):
        s = """rule("%s") {
pattern = "%s"
bold = true
foreground {
    red = %i
    green = %i
    blue = %i
    }
}

        """ %(name, word, self.rgb_dict[color][0],
              self.rgb_dict[color][1], self.rgb_dict[color][2])
        return s
    
# PPHW: a set of rules for syntax highlighting
    def make_basic_son(self):
        highlight_str = ''

        # PPHW: these phrases will all appear in blue (default)
        for i in ['simulation', ' control ', ' archetypes ',
                  ' facility ', ' region ', ' recipe ']:
            highlight_str += self.highlight_maker(i, i)
        # highlight_str += highlight_maker('brack_open', '{', 'red')
        # highlight_str += highlight_maker('brack_close', '}', 'red')
        # highlight_str += highlight_maker('square_open', '[', 'lime')
        # highlight_str += highlight_maker('square_close', ']', 'lime')

        # PPHW: all quoted strings will appear in yellow-ish color
        highlight_str += '''rule("Quoted string") {
pattern = """'[^']*'|"[^"]*""""
bold = true
foreground {
    red = 255
    green = 130
    blue = 0
    }
background {
    red = 255
    green = 130
    blue = 0
    alpha = 25
    }
}

rule("equal"){
pattern="="
background{
    red=192
    green=192
    blue=192
    }
}

rule("Comment") {
    pattern = "%.*"
    italic = true
    foreground {
        red = 0
        green = 128
        blue = 0
    }
}

'''
        return highlight_str

class generate_schema:
    def __init__(self, cyclus_cmd, metadata_path='/Users/4ib/Desktop/git/cyclus_gui/neams/m.json'):
        # define how to run cyclus
        self.cyclus_cmd = cyclus_cmd
        # cross-listing of types: XML <-> SON
        self.conversion_dict = {'string': 'String',
                                'nonNegativeInteger': 'Int',
                                'boolean': 'Int',
                                'double': 'Real',
                                'positiveInteger': 'Int',
                                'float': 'Real',
                                'double': 'Real',
                                'duration': 'Int',
                                'integer': 'Int',
                                'nonPositiveInteger': 'Int',
                                'negativeInteger': 'Int',
                                'long': 'Real',
                                'int': 'Int',
                                'token': 'String'
                                }
        # default schema (grammar) for a Cyclus SON file
        # hand-coded version of standard Cyclus XML Schema
        # to get XML Schema type command: cyclus --schema
        self.sch_str = sch_str = """simulation {
    Description="Agent-based fuel cycle simulator"
    InputTmpl="init_template"
    control {  
             MinOccurs=1
             Description="Defines simulation time and decay methods"
             MaxOccurs=1
             duration={
                 MinOccurs=1
                 MaxOccurs=1
                 Description="the number of timesteps in simulation"
                 ValType=Int
                 }
             startyear={
                 MinOccurs=1
                 MaxOccurs=1
                 Description="the year to start the simulation"
                 ValType=Int
                 }
             startmonth={
                 MinOccurs=1
                 MaxOccurs=1
                 Description="the month to start the simulation"
                 ValType=Int
                 ValEnums=[ 1 2 3 4 5 6 7 8 9 10 11 12 ]
                 }
             decay={
                 MinOccurs=0
                 MaxOccurs=1
                 Description="How to model decay in Cyclus"
                 ValType=String
                 ValEnums=["lazy" "manual" "never"]
                 }
             dt={
                 MinOccurs=0
                 MaxOccurs=1
                 ValType=Real
                 Description="duration of a single timestep in seconds"
                 }
             explicit_inventory={
                 MinOccurs=0
                 MaxOccurs=1
                 ValType=Int
                 ValEnums=[0 1]
                 Description="boolean specifying whether or nor to track inventory in each agent"
                 }
             
            }

    archetypes {
        MinOccurs=1
        Description="Defines the archetypes used in this simulation"
        MaxOccurs=1
        spec={
            MinOccurs=1
            lib={MinOccurs=1
                 MaxOccurs=1
                 ValType=String
                }
            name={MinOccurs=1
                 MaxOccurs=1
                 ValType=String
                 }
            }
    }
    
    facility {
        name= {MinOccurs=1
               MaxOccurs=1
               ValType=String}
        Description="Facility definition block"
        MinOccurs=1
        config = {MinOccurs=1
                  MaxOccurs=1
                  $$facility_enums
                  $$facility_schema}
    }
    
    region{
        Description="Region definition block"
        name= {MinOccurs=1
               MaxOccurs=1
               ValType=String}
        MinOccurs=1
        config= {MinOccurs=1
                 MaxOccurs=1
                 $$region_enums
                 $$region_schema
                 }
        institution={MinOccurs=1
                     name= {MinOccurs=1
                            MaxOccurs=1
                            ValType=String}
                    config={MinOccurs=1
                            MaxOccurs=1
                            $$institution_enums
                            $$institution_schema}
                    initialfacilitylist={MaxOccurs=1
                                          entry={MinOccurs=1
                                                 number={MaxOccurs=1
                                                         ValType=Int}
                                                 prototype={MaxOccurs=1
                                                            ValType=String}
                                                }
                                         }
                    }
    }
    
    recipe{
        Description="Recipe definition block"
        name={
            MinOccurs=1
            MaxOccurs=1
            ValType=String
            }
        basis={
            MinOccurs=1
            MaxOccurs=1
            ValType=String
            ValEnums=["mass" "atom"]
            }
        nuclide={
            MinOccurs=1
            id={MinOccurs=1 MaxOccurs=1}
            comp={MinOccurs=1 MaxOccurs=1 ValType=Real}
            }
    }

}
"""
        # PPHW: basic template to start a new file
        self.init_template = """simulation{

    control {
        duration = 1234
        startmonth = 1
        startyear = 2020
        explicit_inventory=0
        dt=2629846
        decay="lazy"
    }
    
    archetypes { % This part is automatically filled! No need to worry
$$spec_string
    }


    facility {
        name="facility_name"
        config {
                % autocomplete here
                }     
    }
    facility {
        name="facility_name"
        config {
                % there can be multiple facilities
                }     
    }

    
    region {
        name="region_name"
        config {
                % autocomplete here
                }
        institution {
                name="inst_name"
                config{
                        % define institution here
                       }
        }
        institution {
                name="inst_name"
                config{
                        % define institution here
                       }
        }
    }
    region {
        name="region_name"
        config {
                % there can be multiple regions
                }
        institution {
                name="inst_name"
                initialfacilitiylist {entry={num=1
                                             prototype=proto
                                             }
                                     }
                config{
                        % define institution here
                       }
        }
        institution {
                name="inst_name"
                initialfacilitiylist {entry={num=1
                                             prototype=proto
                                             }
                                     }
                config{
                        % define institution here
                       }
        }
    }

    
    recipe {
        % this is an example
        basis="mass"
        name="natl_u"
        nuclide={comp=0.997 id="u238"}
        nuclide={comp=0.003 id="u235"}
    }
    recipe {
        %there can be multiple recipes
    }
}"""
        self.get_cyclus_files()



    def get_cyclus_files(self):
        # this is where everything happens
        
        # temporary !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

        # PPHW: Read the metadata, either from a Cyclus run or saved metadata file
        try:
          p = subprocess.Popen([self.cyclus_cmd, '-m'], stdout=subprocess.PIPE)
          meta_str = p.stdout.read()
          self.meta_dict = json.loads(meta_str) 
        except:
          print('Could not run Cyclus, replacing metadata file with a pre-stored one..')        
          heredir = os.path.abspath(os.path.dirname(__file__))
          self.meta_dict = json.loads(open(os.path.join(heredir, 'm.json')).read())
        
        # temporary !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        
        # PPHW: read list of archetypes from the metadata
        archetypes = self.meta_dict['specs']
        # reading them all
        self.schema_dict = {}
        self.template_dict = {}
        self.type_dict = {}
        spec_string = ''

        # PPHW: go through each archetype to understand its contents
        for arche in archetypes:

            # PPHW: extract archetype name from arche
            name = arche.split(':')[-1]

            # PPHW: create an entry in the type dictionary for this archetype by reading its entity type from metadata
            self.type_dict[name] = self.meta_dict['annotations'][arche]['entity']
            self.schema_dict[name] = {'InputTmpl': '"%s"' %name.encode('ascii')}

            # PPHW: make a valid input file line for a spec using the library name and archetype name extracted from arche
            spec_string += ' '*16 + 'spec = {lib="%s" name="%s"}\n' %(arche.split(':')[1], arche.split(':')[2])

            # PPHW: If this is a NullRegion or NullInst, its template is empty
            # PPHW: bad practice - hardcoded specific archetypes
            if 'NullRegion' in arche or 'NullInst' in arche:
                self.template_dict[name] = name+r'={}'
                continue

            # PPHW: convert XML schema to SON from inside metadata
            d = dict(xml2obj(self.meta_dict['schema'][arche])._attrs)
            #d = xmltodict.parse(self.meta_dict['schema'][arche])['interleave']

            # PPHW: check what is in the dictionary that was made out of the XML Schema
            k = self.check_if_list(d['element'])
            for i in k:
                self.schema_dict[name].update(self.read_element(dict(i._attrs)))
            k = self.check_if_list(d['optional'])
            for i in k:
                self.schema_dict[name].update(self.read_element(dict(i.element._attrs), optional=True))
            if self.type_dict[name] == 'facility':
                tab = ' ' * 16
            elif self.type_dict[name] == 'region':
                tab = ' ' * 16
            elif self.type_dict[name] == 'institution':
                tab = ' ' * 25
            self.template_dict[name] = self.schema_dict_string_to_template(self.schema_dict[name], arche, tab)

            # fill in init_template to have the archetypes


        self.init_template = self.init_template.replace('$$spec_string', spec_string)
        self.template_dict['init_template'] = self.init_template

        # get all the strings for the schema file
        schema_str_dict = {'facility': '',
                           'region': '',
                           'institution': ''}
        for key, val in self.schema_dict.items():
            t = self.type_dict[key]
            if t == 'facility':
                tab = '\t'*3
            elif t == 'region':
                tab = '\t'*3
            elif t == 'institution':
                tab = '\t'*5

            if schema_str_dict[t] != '':
                schema_str_dict[t] += tab[:-1]  
            schema_str_dict[t] += key + '=\n'
            schema_str_dict[t] += tab + self.schema_dict_entry_to_schema_string(val).replace('\n', '\n'+tab)
            schema_str_dict[t] += '\n'



        for key, val in schema_str_dict.items():
            self.sch_str = self.sch_str.replace('$$%s_schema' %key, val)

        for t in ['facility', 'institution', 'region']:
            poss_arches = [x for x, y in self.type_dict.items() if y==t]
            self.sch_str = self.sch_str.replace('$$%s_enums' %t, 'ChildExactlyOne = [' + ' '.join(poss_arches) + ']')




    def read_element(self, eld, from_one_or_more=False, optional=False):
        if 'interleave' in eld.keys():
            s = self.read_interleave(eld['interleave'], eld['name'], from_one_or_more, optional)
            return s

        # now there's optional and non-optional
        keys = eld.keys()
        if not from_one_or_more:
            options = {'MaxOccurs': 1}
        else:
            options = {}
        if not optional:
            options['MinOccurs'] = 1
            
        s = {eld['name'].encode('ascii'): options}
        if 'oneOrMore' in keys:
            # s = {eld['@name']: {}}
            s[eld['name']].update(self.read_element(dict(eld['oneOrMore']['element']._attrs),
                                  from_one_or_more=True)
                                  )           
            return s

        if 'data' in keys:
            options['ValType'] = self.conversion_dict[eld['data']['type']].encode('ascii')
            s[eld['name']] = options
            return s


    def schema_dict_entry_to_schema_string(self, e):
        schema_string = pprint.pformat(e)
        schema_string = schema_string.replace(',', '')
        schema_string = schema_string.replace("'", '')
        schema_string = schema_string.replace(': ', '=')
        return schema_string



    def reasonable_linebreak(self, string, lim=60):
        nlines = len(string) // lim
        space_indices = []
        for i in range(nlines):
            n = (i+1)*lim
            space_indices.append(string[n:].find(' ') + n)

        new_str = ''
        for indx, val in enumerate(string):
            if indx not in space_indices:
                new_str += val
            else:
                new_str += val + '\n'

        return new_str


    def check_if_list(self, d):
        # this is because some schemas,
        # if there's only one entry would have
        # a dictionary, while if there's multiple
        # would have a list
        if 'ict' in str(type(d)):
            return [d]
        else:
            return d


    def schema_dict_string_to_template(self, d, key, tab='\t'):
        name = key.split(':')[-1]
        prev_bracket_location = 0
        c = copy.deepcopy(d)
        d = {name: d}
        s = pprint.pformat(self.delete_keys_from_dict(c, ['MaxOccurs', 'MinOccurs', 'ValType']))
        s = s[1:]
        s = '\n'.join(s.split('\n'))
        s = s[:-1]
        s = s.replace("'", '').replace(',', '').replace(':', '').replace('"', '')
        s = s.split('\n')
        n = self.reasonable_linebreak(self.meta_dict['annotations'][key]['doc']).split('\n') + ['']
        n = ['%'+w for w in n]
        n.append(name + ' {')
        for i in s:
            var = i.strip().split()[0]
            # print(self.schema_dict[name].keys())
            # if var == 'streams':
            #    var = 'streams_'
            if var == 'InputTmpl':
                continue
            if var not in self.schema_dict[name].keys():
                # multiline variables with weird things
                skipallthat = True
            else:
                skipallthat = False

            if not skipallthat:
              # see if optional
              if 'MinOccurs' not in self.schema_dict[name][var]:
                  optional = '(optional)'
              else:
                  optional = ''
              t = ''
              try:
                  if var == 'streams':
                    t = self.meta_dict['annotations'][key]['vars']['streams_']['type']
                    doc = self.reasonable_linebreak(optional + ' [%s] ' %t +self.meta_dict['annotations'][key]['vars']['streams_']['doc'] ).split('\n')
                    
                  else:
                    t = self.meta_dict['annotations'][key]['vars'][var]['type']
                    doc = self.reasonable_linebreak(optional + ' [%s] ' %t +self.meta_dict['annotations'][key]['vars'][var]['doc'] ).split('\n')
              except:
                  doc = [optional + ' [%s] '%t + 'no doc available.']
              for j in doc:
                  #if j == doc[0]:
                  n.append(tab+ '\t%' + j)
              line = tab + i.strip().replace('{}', '=')
              n.append(line)
              # this is saved just for later
              prev_bracket_location = line.rfind('{') + 1
              #if i.count('{') == 1:
              #  n.append(tab + i.strip().replace(' {', '=').replace('}', ''))
              #else:
              #  n.append(tab + i.strip().replace('{}', '='))
              if optional:
                default = self.meta_dict['annotations'][key]['vars'][var]['default']
                if isinstance(default, str):
                  default = '"' + default + '"'
                if isinstance(default, list):
                  result = re.search('{(.*)}', n[-1]).group(1)
                  default = '   %% The value can be multiple values of %s' %result.strip().replace('=', '')
                n[-1] = n[-1] + str(default)


            else:
              # if the variable has some sort of nested input structure
              line = ' '*prev_bracket_location + i.strip().replace('{}', '=')
              prev_bracket_location = line.rfind('{') + 1
              count = line.count('}') - 1
              locs = []
              indices = []
              k = 1
              while count > 0:
                # close them brackets in the appropriate location newline
                  indices = [w for w, va in enumerate(n[-k]) if va == '{']
                  count -= len(indices)
                  line = line.replace('}', '', len(indices))
                  locs.extend(indices[::-1])
                  k +=1
              n.append(line)
              for j in locs:
                n.append(' '*j + '}')        
            n.append('')

        n.append('}')
        return '\n'.join(n)


    def delete_keys_from_dict(self, dict_del, lst_keys):
        for k in lst_keys:
            try:
                del dict_del[k]
            except KeyError:
                pass
        for v in dict_del.values():
            if isinstance(v, dict):
                self.delete_keys_from_dict(v, lst_keys)

        return dict_del


    def read_interleave(self, intd, name, from_one_or_more, optional):
        if not optional:
            options = {'MinOccurs':1}
        else:
            options = {}
        if not from_one_or_more:
            options['MaxOccurs'] = 1
        d = {name.encode('ascii'): options}
        for i in intd['element']:
            d[name].update(self.read_element(dict(i._attrs)))
        return d


here = os.path.dirname(os.path.abspath(__file__))
def generate_cyclus_workbench_files(workbench_rte_dir,
                                    cyclus_cmd):
    # settings part
    cyclus_dir = os.path.join(workbench_rte_dir, 'cyclus')
    if not os.path.exists(cyclus_dir):
        os.mkdir(cyclus_dir)
    etc_dir = os.path.join(workbench_rte_dir, os.pardir, 'etc')
    # define paths
    schema_path = os.path.join(cyclus_dir, 'cyclus.sch')
    template_dir = os.path.join(etc_dir, 'Templates', 'cyclus')
    highlight_path = os.path.join(etc_dir, 'grammars', 'highlighters', 'cyclus.wbh')
    grammar_path = os.path.join(etc_dir, 'grammars', 'cyclus.wbg')



    grammar_str  = """name= Cyclus
enabled = true

parser = waspson
schema = "%s"
validator = wasp

templates = "%s"

highlighter = "%s"

extensions = [cyclus]
maxDepth = 10
""" %(schema_path, template_dir, highlight_path)

    # write the files
    with open(grammar_path, 'w') as f:
        print('Wrote grammar file at:')
        print(grammar_path)
        f.write(grammar_str)
    # extra copy for giggles
    with open(schema_path.replace('.sch', '.wbg'), 'w') as f:
        f.write(grammar_str)

    s_ = generate_schema(cyclus_cmd)
    with open(schema_path, 'w') as f:
        print('Wrote schema file at:')
        print(schema_path)
        f.write(s_.sch_str)

    # create template directory if it doesn't exist
    if not os.path.exists(template_dir):
        os.mkdir(template_dir)
    print('Writing template files on %s:' %template_dir)
    for key, val in s_.template_dict.items():
        with open(os.path.join(template_dir, key+'.tmpl'), 'w') as f:
            print('\tWrote template for %s at:' %key)
            print('\t'+os.path.join(template_dir, key+'.tmpl'))
            f.write(val)

    h_ = highlighter()
    with open(highlight_path, 'w') as f:
        print('Wrote highlight file at:')
        print(highlight_path)
        f.write(h_.highlight_str)


    # copy the cyclus.py file
    shutil.copyfile(os.path.join(here, 'cyclus.py'), os.path.join(workbench_rte_dir, 'cyclus.py'))
    print('Copied cyclus runner to:')
    print(os.path.join(workbench_rte_dir, 'cyclus.py'))
    shutil.copyfile(os.path.join(here, 'cyclus_processor.py'), os.path.join(workbench_rte_dir, 'cyclus', 'cyclus_processor.py'))
    print('Copied cyclus processor to:')
    print(os.path.join(workbench_rte_dir, 'cyclus', 'cyclus_processor.py'))    
    shutil.copyfile(os.path.join(here, 'cyclus.wbp'), os.path.join(etc_dir, 'processors', 'cyclus.wbp'))
    print('Copied cyclus processor file to:')
    print(os.path.join(etc_dir, 'processors', 'cyclus.wbp'))
    
    print('Done!\n\n')



def clean_xml(s):
    new = []
    indx = 0
    lines = s.split('\n')
    while indx < len(lines):
        line = lines[indx]
        if '<value>' in line:
            line = line.replace('<value>', '').replace(r'</value>', '').replace('\n', '').strip()
            if line == 'null':
                line = ''
            closing = new[-1].strip().replace('<',r'</')
            new[-1] = new[-1].replace('\n', '') + line + closing
            indx += 1
        else:
            new.append(line)
        indx += 1
    return '\n'.join(new)



if __name__ == '__main__':
    # modify this for your setup!
    # make sure your slashes are os appropriate
    path = '/Users/4ib/Downloads/Workbench-Darwin/rte'
    cyclus_cmd = 'cyclus'
    generate_cyclus_workbench_files(workbench_rte_dir=path,
                                    cyclus_cmd=cyclus_cmd)