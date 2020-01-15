import xmltodict
import copy
import numpy as np
import json
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
        for i in ['simulation', 'control', 'archetypes',
                  'facility', 'region', 'recipe']:
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

'''
        return highlight_str

class generate_schema:
    def __init__(self, cyclus_cmd):
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
        self.sch_str = sch_str = """simulation{
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
        Description="Facility definition block"
        MinOccurs=1
        config = {MinOccurs=1
                  MaxOccurs=1
                  $$facility_enums
                  $$facility_schema}
    }
    
    region{
        Description="Region definition block"
        MinOccurs=1
        config= {MinOccurs=1
                 MaxOccurs=1
                 $$region_schema
                 }
        institution={MinOccurs=1
                    config={MinOccurs=1
                             MaxOccurs=1
                             $$institution_schema}
                    initialfacilitiylist={MaxOccurs=1
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
        config {"autocomplete here"}     
    }
    facility {
        config {"there can be multiple facilities"}     
    }

    
    region {
        config {"autocomplete here"}
    }
    region {
        config {"there can be multiple regions"}
    }

    
    recipe {
        "write your recipes here"
    }
    recipe {
        "there can be multiple recipes"
    }
}"""
        self.get_cyclus_files()



    def get_cyclus_files(self):
        # this is where everything happens
        
        # temporary !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # meta_str = subprocess.run([self.cyclus_cmd, '-m'], stdout=subprocess.PIPE, shell=True).stdout.decode('utf-8') 
        # self.meta_dict = json.loads(meta_str) 
        self.meta_dict = json.loads(open('m.json').read())        
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
                continue
            d = xmltodict.parse(self.meta_dict['schema'][arche])['interleave']
            k = self.check_if_list(d['element'])
            for i in k:
                self.schema_dict[name].update(self.read_element(i))
            k = self.check_if_list(d['optional'])
            for i in k:
                self.schema_dict[name].update(self.read_element(i['element'], optional=True))

            if self.type_dict[name] == 'facility':
                tab = '\t'*3
            elif self.type_dict[name] == 'region':
                tab = '\t'*3
            elif self.type_dict[name] == 'institution':
                tab = '\t'*5
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

        poss_arches = [x for x, y in self.type_dict.items() if y=='facility']
        self.sch_str = self.sch_str.replace('$$facility_enums', 'ValEnums = [' + ' '.join(poss_arches) + ']')



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
        c = copy.deepcopy(d)
        d = {name: d}
        s = pprint.pformat(self.delete_keys_from_dict(c, ['MaxOccurs', 'MinOccurs', 'ValType']))
        s = s[1:]
        s = '\n'.join(s.split('\n'))
        s = s[:-1]
        s = s.replace("'", '')
        s = s.replace(',', '')
        s = s.replace(':', '')
        s = s.replace('"', '')
        s = s.split('\n')
        n = self.reasonable_linebreak(self.meta_dict['annotations'][key]['doc']).split('\n') + ['']
        n = [tab+'%'+w for w in n]
        for i in s:
            var = i.strip().split()[0]
            if var == 'streams':
                var = 'streams_'
            if var == 'InputTmpl':
                continue
            if var not in self.schema_dict[name].keys():
                # multiline variables with weird things
                print('skipping', var)
                continue
            # see if optional
           
            if 'MinOccur' not in d[name][var]:
                optional = '(optional)'
            else:
                optional = ''
            try:
                doc = self.reasonable_linebreak(optional + ' ' +self.meta_dict['annotations'][key]['vars'][var]['doc'] ).split('\n')
            except:
                doc = optional + 'no doc available.'
            for j in doc:
                n.append(tab+'%' + j)
            n.append(tab + i.strip())

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






def main(schema_path='/Users/4ib/Desktop/git/cyclus_gui/neams/cyclus.sch',
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
""" %(schema_path, template_dir, highlight_path)

    # write the files
    with open(grammar_path, 'w') as f:
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

