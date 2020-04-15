import xmltodict
import copy
import numpy as np
import json
import re
import os
import subprocess
import pprint



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
    

    def make_basic_son(self):
        highlight_str = ''
        for i in ['simulation', ' control ', ' archetypes ',
                  ' facility ', ' region ', ' recipe ']:
            highlight_str += self.highlight_maker(i, i)
        # highlight_str += highlight_maker('brack_open', '{', 'red')
        # highlight_str += highlight_maker('brack_close', '}', 'red')
        # highlight_str += highlight_maker('square_open', '[', 'lime')
        # highlight_str += highlight_maker('square_close', ']', 'lime')
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
        self.cyclus_cmd = cyclus_cmd
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
        p = subprocess.Popen([self.cyclus_cmd, '-m'], stdout=subprocess.PIPE)
        meta_str = p.stdout.read()
        self.meta_dict = json.loads(meta_str) 
        #heredir = os.path.abspath(os.path.dirname(__file__))
        #self.meta_dict = json.loads(open(os.path.join(heredir, 'm.json')).read())        
        # temporary !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        
        archetypes = self.meta_dict['specs']
        # reading them all
        self.schema_dict = {}
        self.template_dict = {}
        self.type_dict = {}
        spec_string = ''
        for arche in archetypes:
            name = arche.split(':')[-1]
            self.type_dict[name] = self.meta_dict['annotations'][arche]['entity']
            self.schema_dict[name] = {'InputTmpl': '"%s"' %name}
            if 'NullRegion' in arche or 'NullInst' in arche:
                self.template_dict[name] = name+'= null'
                continue
            d = xmltodict.parse(self.meta_dict['schema'][arche])['interleave']
            k = self.check_if_list(d['element'])
            for i in k:
                self.schema_dict[name].update(self.read_element(i))
            k = self.check_if_list(d['optional'])
            for i in k:
                self.schema_dict[name].update(self.read_element(i['element'], optional=True))

            if self.type_dict[name] == 'facility':
                tab = ' ' * 16
            elif self.type_dict[name] == 'region':
                tab = ' ' * 16
            elif self.type_dict[name] == 'institution':
                tab = ' ' * 25
            self.template_dict[name] = self.schema_dict_string_to_template(self.schema_dict[name], arche, tab)

            # fill in init_template to have the archetypes

            spec_string += ' '*16 + 'spec = {lib="%s" name="%s"}\n' %(arche.split(':')[1], arche.split(':')[2])

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
            s = self.read_interleave(eld['interleave'], eld['@name'], from_one_or_more, optional)
            return s

        # now there's optional and non-optional
        keys = eld.keys()
        if not from_one_or_more:
            options = {'MaxOccurs': 1}
        else:
            options = {}
        if not optional:
            options['MinOccurs'] = 1
            
        s = {eld['@name']: options}
        www = np.random.uniform(0, 10)
        if 'oneOrMore' in keys:

            # s = {eld['@name']: {}}
            s[eld['@name']].update(self.read_element(eld['oneOrMore']['element'],
                                   from_one_or_more=True)
                                  )           
            return s

        if 'data' in keys:
            options['ValType'] = self.conversion_dict[eld['data']['@type']]
            s[eld['@name']] = options
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
        d = {name: options}
        for i in intd['element']:
            d[name].update(self.read_element(i))
        return d



def generate_cyclus_workbench_files(schema_path='/Users/4ib/Desktop/git/cyclus_gui/neams/cyclus.sch',
         template_dir='/Users/4ib/Desktop/git/cyclus_gui/neams/templates/',
         highlight_path='/Users/4ib/Desktop/git/cyclus_gui/neams/cyclus.wbh',
         grammar_path='/Users/4ib/.workbench/2.0.0/grammars/cyclus.wbg',
         cyclus_cmd='cyclus'):
    # settings part
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
        f.write(grammar_str)
    # extra copy for giggles
    with open(schema_path.replace('.sch', '.wbg'), 'w') as f:
        f.write(grammar_str)

    s_ = generate_schema(cyclus_cmd)
    with open(schema_path, 'w') as f:
        f.write(s_.sch_str)

    for key, val in s_.template_dict.items():
        with open(os.path.join(template_dir, key+'.tmpl'), 'w') as f:
            f.write(val)

    h_ = highlighter()
    with open(highlight_path, 'w') as f:
        f.write(h_.highlight_str)



#if __name__ == '__main__':
#    generate_cyclus_workbench_files()