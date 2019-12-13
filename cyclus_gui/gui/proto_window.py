from pprint import pprint
from tkinter import *
from tkinter import messagebox
from tkinter import filedialog
from tkinter.scrolledtext import ScrolledText
import xmltodict
import uuid
import os
import shutil
import json
import copy
from window_tools import *
from read_xml import *
from hovertip import CreateToolTip

class PrototypeWindow(Frame):
    def __init__(self, master, output_path):
        """
        proto_dict looks like:
        key: name
        val: dict
            key: archetype, config
                            key: archetype
                            val: dict
                                 key: parameter
                                 val: list or float

        """
        
        self.master = Toplevel(master)
        self.master.title('Add Facilities')
        self.output_path = output_path
        self.master.geometry('+0+700')
        self.guide()
        Label(self.master, text='Choose a facility archetype to add:').grid(row=0)
        self.get_schema()
        self.proto_dict = {}
        self.arche_dict = {}
        self.region_dict = {}
        self.arches, w = read_xml(os.path.join(self.output_path, 'archetypes.xml'), 'arche')
        if os.path.isfile(os.path.join(self.output_path, 'facility.xml')):
            self.proto_dict, self.arche_dict, self.n = read_xml(os.path.join(self.output_path, 'facility.xml'),
                                                                'facility')

        self.region_window()
        self.tkvar = StringVar(self.master)
        archetypes = [x[0] + ':' + x[1] for x in self.arches]
        archetypes = [x for x in archetypes if 'inst' not in x.lower()]
        archetypes = [x for x in archetypes if 'region' not in x.lower()]
        self.tkvar.set('\t\t')
        OptionMenu(self.master, self.tkvar, *archetypes).grid(row=1)
        self.tkvar.trace('w', self.definition_window)

        Button(self.master, text='Done', command= lambda : self.submit()).grid(row=2)

        self.update_loaded_modules()


    def region_window(self):
        # reading regions
        n = 0
        if os.path.isfile(os.path.join(self.output_path, 'region.xml')):
            self.region_dict, n = read_xml(os.path.join(self.output_path, 'region.xml'),
                                        'region')
        self.region_status_window = Toplevel(self.master)
        self.region_status_window.geometry('+500+920')
        c_dict = {'Region': 'pale green',
                  'Institution': 'light salmon',
                  'Facility_proto': 'SkyBlue1',
                  'n_build': 'ivory3',
                  'build_time': 'orchid1',
                  'lifetime': 'pale turquoise'}
        parent = self.region_status_window
        parent = assess_scroll_deny(n+len(self.region_dict.keys())*2+1, self.region_status_window)
        Label(parent, text='Current regions:', bg='yellow').grid(row=0, columnspan=7)
        columns = ['Region', 'Institution', 'Facility_proto', 'n_build', 'build_time', 'lifetime']
        for indx, val in enumerate(columns):
            c = c_dict[val]
            Label(parent, text=val, bg=c).grid(row=1, column=indx+1)
        row = 2
        for regionname, instdict in self.region_dict.items():
            Label(parent, text=regionname, bg='pale green').grid(row=row, column=1)
            row += 1
            for instname, instarray in instdict.items():
                Label(parent, text=instname, bg='light salmon').grid(row=row, column=2)
                row += 1
                for instlist in instarray:
                    fac_name = instlist[0]
                    columns_ = columns[2:]
                    for indx, v in enumerate(instlist):
                        c = c_dict[columns_[indx]]
                        Label(parent, text=v, bg=c).grid(row=row, column=indx+3)
                    row += 1


    def update_status_window(self):
        self.status_window = Toplevel(self.master)
        self.status_window.title('Defined facility prototypes')
        self.status_window.geometry('+250+700')
        parent = self.status_window
        parent = assess_scroll_deny(len(self.proto_dict.keys())+2, self.status_window)
        
        Label(parent, text='Defined Facility Prototypes:\n', bg='yellow').grid(row=0, columnspan=2)
        row=1
        for name, val in self.proto_dict.items():
            string = '%s (%s)\n' %(name, val['archetype'])
            Button(parent, text=string, command = lambda name=name, val=val: self.reopen_def_window(name, val['archetype'])).grid(row=row, column=0)
            Button(parent, text='x', command = lambda name=name: self.delete_fac(name)).grid(row=row, column=1)
            row += 1


    def delete_fac(self, name):
        messagebox.showinfo('Deleted', 'Deleted facility prototype %s' %name)
        self.proto_dict.pop(name, None)
        self.update_loaded_modules()


    def reopen_def_window(self, name, archetype):
        self.def_window = Toplevel(self.master)
        self.def_window.title('Define facility prototype')
        self.def_window.geometry('+700+1000')
        Label(self.def_window, text='%s' %archetype).grid(row=0, columnspan=2)
        proto_name_entry = Entry(self.def_window)
        proto_name_entry.grid(row=1, column=1)
        proto_name_entry.insert(END, name)

        arche_long = self.arche_dict[name]
        Button(self.def_window, text='Done', command=lambda : self.submit_proto(arche_long, proto_name_entry.get())).grid(row=0, column=2)
        Label(self.def_window, text='Prototype Name:').grid(row=1, column=0)

        if arche_long in self.param_dict.keys():
            self.def_entries(arche_long)
            for param, val in self.proto_dict[name]['config'][archetype].items():
                rownum = list(self.entry_dict[param].keys())[0]
                if isinstance(val, dict):
                    try:
                        tag = self.tag_dict[arche_long][param]
                    except:
                        tag = self.tag_dict[arche_long][param+ '*']

                    if not isinstance(val[tag], list):
                        val[tag] = [val[tag]]
                    for ii_, v in enumerate(val[tag]):
                        if ii_ != 0:
                            self.add_entry(param, rownum)
                        self.entry_dict[param][rownum][-1].insert(END, v)
                else:
                    if self.entry_dict[param][rownum].get() != val:
                        self.entry_dict[param][rownum].delete(0, END)
                        self.entry_dict[param][rownum].insert(END, val)
        else:
            self.def_entries_unknown(archetype, name=name, reopen=True)


    def get_schema(self):
        # get from cyclus -m
        path = os.path.join(self.output_path, 'm.json')
        if os.path.isfile(path):
            with open(path, 'r') as f:
                jtxt = f.read()
            self.j = json.loads(jtxt)

        else:
            messagebox.showinfo('Cyclus not found', 'We have automated documentation from packaged json, since Cyclus is not found on your computer.')
            with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), '../..', 'src/metadata.json'), 'r') as f:
                jtxt = f.read()
            self.j = json.loads(jtxt)

        # get documentation for variable and archetype
        self.doc_dict = {}
        self.type_dict = {}
        self.default_dict = {}
        for arche, cat_dict in self.j['annotations'].items():
            arche = arche[1:]
            self.doc_dict[arche] = {}
            self.type_dict[arche] = {}
            self.default_dict[arche] = {}
            self.doc_dict[arche]['arche'] = cat_dict['doc']
            for key, val in cat_dict['vars'].items():
                try:
                    if 'doc' in val.keys():
                        docstring = val['doc']
                    elif 'tooltip' in val.keys():
                        docstring = val['tooltip']
                    else:
                        docstring = 'No documentation avail.' 

                    if 'default' in val.keys():
                        self.default_dict[arche][key] = val['default']

                    self.type_dict[arche][key] = val['type']
                except:
                    docstring = 'No documentation avail.'
                
                self.doc_dict[arche][key] = docstring

        self.tag_dict = {}
        self.param_dict = {}
        self.j['schema'] = {k:v for k,v in self.j['schema'].items() if 'region' not in k.lower()}
        self.j['schema'] = {k:v for k,v in self.j['schema'].items() if 'inst' not in k.lower()}
        for arche, xml in self.j['schema'].items():
            arche = arche[1:]
            schema_dict = xmltodict.parse(xml)
            self.tag_dict[arche] = {}
            self.param_dict[arche] = {'oneormore': [],
                                 'one': []}
            if 'interleave' not in schema_dict.keys():
                continue
            for op_el in schema_dict['interleave']:
                if op_el == 'element':
                    optional = False
                else:
                    optional = True
                if isinstance(schema_dict['interleave'][op_el], list):
                    for param in schema_dict['interleave'][op_el]:
                        if 'element' in param.keys():
                            param = param['element']
                        name = param['@name']
                        if optional:
                            name += '*'
                        if 'interleave' in param:
                            continue
                        if 'data' in param:
                            self.param_dict[arche]['one'].append(name)
                            continue
                        if 'oneOrMore' in param:
                            self.param_dict[arche]['oneormore'].append(name)
                            self.tag_dict[arche][name] = param['oneOrMore']['element']['@name']
                            if 'interleave' in param['oneOrMore']['element'].keys():
                                continue
                else:
                    param = schema_dict['interleave'][op_el]
                    if 'element' in param.keys():
                        param = param['element']
                    name = param['@name']
                    if optional:
                        name += '*'
                    if 'interleave' in param:
                        continue
                    if 'data' in param:
                        self.param_dict[arche]['one'].append(name)
                        continue
                    if 'oneOrMore' in param:
                        self.param_dict[arche]['oneormore'].append(name)
                        self.tag_dict[arche][name] = param['oneOrMore']['element']['@name']
                        if 'interleave' in param['oneOrMore']['element'].keys():
                            continue


    def update_loaded_modules(self):
        try:
            self.status_window.destroy()
        except:
            z=0
        self.update_status_window()


    def submit(self):
        new_dict = {'root': {'facility': []}}
        if len(self.proto_dict) == 0:
            messagebox.showerror('Nope', 'You have not defined any facilities yet.')
            return
        self.not_defined = []
        for regionname, instdict in self.region_dict.items():
            for instname, instarray in instdict.items():
                for instlist in instarray:
                    if instlist[0] not in self.proto_dict.keys():
                        self.not_defined.append(instlist[0])
        if len(self.not_defined) != 0:
            string = 'You have not defined:\n'
            for i in self.not_defined:
                string += '%s\n' %i
            messagebox.showerror('Nope', string)
            return
        with open(os.path.join(self.output_path, 'facility.xml'), 'w') as f:
            for name, config in self.proto_dict.items():
                facility_dict = {}
                facility_dict['name'] = name
                facility_dict['config'] = config['config']
                new_dict['root']['facility'].append(facility_dict)
            f.write(xmltodict.unparse(new_dict, pretty=True))
        messagebox.showinfo('Sucess', 'Successfully rendered %i facility prototypes!' %len(new_dict['root']['facility']))
        self.master.destroy()
        self



    def definition_window(self, *args):
        self.def_window = Toplevel(self.master)
        self.def_window.title('Define facility prototype')
        self.def_window.geometry('+700+1000')
        archetype = self.tkvar.get()
        Label(self.def_window, text='%s' %archetype).grid(row=0, columnspan=2)

        proto_name_entry = Entry(self.def_window)
        proto_name_entry.grid(row=1, column=1)
        Button(self.def_window, text='Done', command=lambda : self.submit_proto(archetype, proto_name_entry.get())).grid(row=0, column=2)
        Label(self.def_window, text='Prototype Name:').grid(row=1, column=0)
        
        if archetype in self.param_dict.keys():
            self.def_entries(archetype)
        else:
            self.def_entries_unknown(archetype)


    def submit_proto(self, archetype, proto_name):
        if proto_name == '':
            messagebox.showerror('Error', 'You must define the prototype name')
            return
        archetype_name = archetype.split(':')[-1]
        config_dict = {archetype_name: {}}
        # if from unknown, parse it through before
        if str(list(self.entry_dict.keys())[0]).replace('-','').isdigit():
            new_entry_dict = {}
            for key, val in self.entry_dict.items():
                # positive is scalar value:
                # [0] parameter name
                # [1] value
                if key > 0:
                    for rownum, val_list in val.items():
                        new_entry_dict[val_list[0].get()] = {rownum: val_list[1]}
                # negative is one or more value:
                # [0] parameter name
                # [1] tag
                # [2 - ] values
                else:
                    for rownum, val_list in val.items():
                        name = val_list[0].get()
                        new_entry_dict[name] = {rownum: []}
                        for i in val_list[2:]:
                            new_entry_dict[name][rownum].append(i)
                        try:
                            self.tag_dict[archetype][name] = val_list[1].get()
                        except:
                            self.tag_dict[archetype] = {name: val_list[1].get()}
            self.entry_dict = new_entry_dict
        # .get() all the entries
        for param, row_val_dict in self.entry_dict.items():
            for rownum, val_list in row_val_dict.items():
                if isinstance(val_list, list):
                    val_list = [x.get() for x in val_list]
                    val_list = [x for x in val_list if x != '']
                    if archetype in self.default_dict.keys():                    
                        if param not in self.default_dict[archetype].keys() and len(val_list) == 0:
                            messagebox.showerror('Error', '%s must be filled out' %param)
                            return
                    if len(val_list) == 0:
                        continue
                    # change tag with param by referencing
                    # tag_dict
                    try:
                        tag = self.tag_dict[archetype][param]
                    except:
                        try:
                            tag = self.tag_dict[archetype][param + '*']
                        except:
                            qq=0
                    val_list = {tag: val_list} 
                if isinstance(val_list, dict):
                    val_list = val_list
                else:
                    val_list = val_list.get()
                    if val_list == '':
                        continue
                    val_list 
                # check for empty values    
                config_dict[archetype_name][param] = val_list
        
        self.arche_dict[proto_name] = archetype
        self.proto_dict[proto_name] = {'archetype': archetype_name,
                                       'config': config_dict}
        messagebox.showinfo('Success', 'Successfully created %s facility %s' %(archetype_name, proto_name))
        self.update_loaded_modules()
        self.def_window.destroy()


    def def_entries(self, archetype):
        """
        entry_dict:
        key: name of entry (e.g. cycle_time)
        val: dict
            key: rownum
            val: entry object list (length = column no.)
        # did not do matrix since the column lengths can be irregular
        """
        start_row = 2
        self.entry_dict = {}

        self.proto_guide_window(archetype)
        oneormore = self.param_dict[archetype]['oneormore']
        if 'streams' in oneormore:
            oneormore.remove('streams')
        if 'in_streams' in oneormore:
            oneormore.remove('in_streams')
        one = self.param_dict[archetype]['one']

        for val in oneormore:
            start_row += 1
            self.add_row_oneormore(val, self.def_window, start_row, archetype)

        for  val in one:
            start_row += 1
            self.add_row(val, self.def_window, start_row, archetype)   
            # add color for non-essential parameters


        start_row += 1
        if archetype == 'cycamore:Separations':
            # special treatment for separations
            # add stream
            Button(self.def_window, text='Add output Stream', command=lambda:self.add_sep_stream()).grid(row=start_row, columnspan=3)
            self.update_stream_status_window()
            self.entry_dict['streams'] = {9999: {'item': []}}

        if archetype == 'cycamore:Mixer':
            Button(self.def_window, text='Add input Stream', command=lambda:self.add_mix_stream()).grid(row=start_row, columnspan=3)
            self.update_mixer_status_window()
            self.entry_dict['in_streams'] = {9999: {'stream': []}}


    def def_entries_unknown(self,archetype, name='', reopen=False):
        """
        entry_dict:
        key: number - positive for scalar, negative for vector
        value: dict
                key: rownum
                val: list of Entry objects
        """
        self.start_row = 2
        self.entry_dict = {}
        self.unknown_window()
        self.unknown_entry = 0
        Button(self.def_window, text='Add scalar', command=lambda:self.add_row('', self.def_window, self.start_row, archetype)).grid(row=self.start_row, column=0)
        Button(self.def_window, text='Add vector', command=lambda:self.add_row_oneormore('', self.def_window, self.start_row, archetype)).grid(row=self.start_row, column=1)
        self.start_row += 1
        Label(self.def_window, text='Parameter').grid(row=self.start_row, column=1)
        Label(self.def_window, text='tag').grid(row=self.start_row, column=2)
        Label(self.def_window, text='Value').grid(row=self.start_row, column=3)
        self.start_row += 1

        if reopen:
            for param, val in self.proto_dict[name]['config'][archetype].items():
                if isinstance(val, dict):
                    # dict = one or more
                    # populate entry blanks
                    self.add_row_oneormore('', self.def_window, self.start_row, archetype)
                    for tag, vallist in val.items():
                        label = self.unknown_entry * -1
                        for i in range(len(vallist)):
                            self.add_entry(label, self.start_row-1)
                    self.entry_dict[label][self.start_row-1][0].insert(END, param)
                    self.entry_dict[label][self.start_row-1][1].insert(END, tag)
                    for indx, i in enumerate(vallist):
                        self.entry_dict[label][self.start_row-1][indx+2].insert(END, i)

                else:
                    # populate entry objects
                    self.add_row('', self.def_window, self.start_row, archetype)
                    label = self.unknown_entry
                    self.entry_dict[label][self.start_row-1][0].insert(END, param)
                    self.entry_dict[label][self.start_row-1][1].insert(END, val)
                
        # button one for value and another for one or more



    def unknown_window(self):
        string = """
        The archetype you are adding is unknown to the schema,
        so it is up to you to know the parameters you need.

        """


    def update_stream_status_window(self):
        try:
            self.stream_status_window.destroy()
        except:
            z=0
        self.stream_status_window = Toplevel(self.def_window)
        Label(self.stream_status_window, text='Defined Streams').grid(row=0, columnspan=2)
        row=1
        if 'streams' in self.entry_dict.keys():
            for st in self.entry_dict['streams'][9999]['item']:
                Button(self.stream_status_window, text=st['commod'], command=lambda st=st:self.update_stream(st['commod'])).grid(row=row, column=0)
                Button(self.stream_status_window, text='x', command=lambda st=st:self.delete_stream(st['commod'])).grid(row=row, column=1)
                row += 1

    def update_stream(self, stream_name):
        self.add_sep_stream()
        for indx, val in enumerate(self.entry_dict['streams'][9999]['item']):
            if stream_name == val['commod']:
                it = indx

        self.commod_entry.insert(END, stream_name)
        self.buf_entry.insert(END, self.entry_dict['streams'][9999]['item'][indx]['info']['buf_size'])
        for indx, item in enumerate(self.entry_dict['streams'][9999]['item'][indx]['info']['efficiencies']['item']):
            self.add_sep_row()
            self.el_ef_entry_list[indx][0].insert(END, item['comp'])
            self.el_ef_entry_list[indx][1].insert(END, item['eff'])

        del self.entry_dict['streams'][9999]['item'][it]

    def delete_stream(self, stream_name):
        for indx, val in enumerate(self.entry_dict['streams'][9999]['item']):
            if stream_name == val['commod']:
                kill = indx
        del self.entry_dict['streams'][9999]['item'][kill]
        self.update_stream_status_window()
        return


    def proto_guide_window(self, archetype):
        proto_guide_window_ = Toplevel(self.def_window)
        proto_guide_window_.title('%s documentation' %archetype)
        proto_guide_window_.geometry('+0+1000')
        string = '**The highlighted parameters mean that they are optional.**\n'
        string += '**The non-highlighted parameters need to be filled in**\n'
        string += '**The parameters with `Add` button next to it can take in multiple values**\n'
        string += '**For descriptions of the parameters, hover your mouse over them!**\n\n\n'
        string += archetype + '\n'

        
        # documentation for archetype
        input_variables = self.param_dict[archetype]['oneormore'] + self.param_dict[archetype]['one']
        input_variables = [x.replace('*', '') for x in input_variables]
        string += self.doc_dict[archetype]['arche'] + '\n\n'

        """
        string += self.doc_dict[archetype]['arche'] + '\n\n' + '========== Parameters ==========\n'
        for key, val in self.doc_dict[archetype].items():
            if key not in input_variables or key == 'arche':
                continue
            if key == 'streams' or key == 'in_streams':
                key = 'streams_'
            string += key + ' (%s'%self.type_dict[archetype][key]
            if key in self.default_dict[archetype].keys():
                default_val = str(self.default_dict[archetype][key])
                if default_val == '':
                    default_val = "''"
                string += ', default=%s' %default_val
            string += '):\n' + val + '\n\n' 
        """
        t = ScrolledText(proto_guide_window_)
        t.pack()
        t.insert(END, string)


    def add_sep_stream(self):
        self.sep_stream_window = Toplevel(self.def_window)
        self.sep_stream_window.title('Stream definition')

        Label(self.sep_stream_window, text='Commodity name').grid(row=0, column=0)
        self.commod_entry = Entry(self.sep_stream_window)
        self.commod_entry.grid(row=0, column=1)
        Label(self.sep_stream_window, text='Buffer size').grid(row=1, column=0)
        self.buf_entry = Entry(self.sep_stream_window)
        self.buf_entry.grid(row=1, column=1)
        self.buf_entry.insert(END, '1e299')
        self.el_ef_entry_list = []
        Button(self.sep_stream_window, text='Done', command=lambda:self.submit_sep_stream()).grid(row=0, column=2)

        Label(self.sep_stream_window, text='Efficiencies:').grid(row=2, columnspan=2)
        Button(self.sep_stream_window, text='Add element', command=lambda:self.add_sep_row()).grid(row=2, column=2)

        Label(self.sep_stream_window, text='Element').grid(row=3, column=0)
        Label(self.sep_stream_window, text='Efficiency (< 1.0)').grid(row=3, column=1)
        self.sep_row_num = 4


    def submit_sep_stream(self):

        sep_stream_dict = {'commod': self.commod_entry.get(),
                           'info': {'buf_size': self.buf_entry.get(),
                                    'efficiencies': {'item': []}}}
        self.el_ef_list = [[x[0].get(), x[1].get()] for x in self.el_ef_entry_list]
        for i in self.el_ef_list:
            if i[0] == i[1] == '':
                continue
            elif i[0] == '' or i[1] == '':
                messagebox.showerror('Error', 'Stream element and efficiency missing')
                return 
            sep_stream_dict['info']['efficiencies']['item'].append({'comp': i[0], 'eff': i[1]})
        if len(sep_stream_dict['info']['efficiencies']['item']) == 0:
            messagebox.showerror('Error', 'You did not define a single stream')
            return
        done = False
        for indx, val in enumerate(self.entry_dict['streams'][9999]['item']):
            if val['commod'] == sep_stream_dict['commod']:
                set_indx = indx
                self.entry_dict['streams'][9999]['item'][set_indx] = sep_stream_dict
                done = True
        if not done:
            self.entry_dict['streams'][9999]['item'].append(sep_stream_dict)
        messagebox.showinfo('Success', 'Succesfully added separation stream')
        self.sep_stream_window.destroy()
        self.update_stream_status_window()


    def add_sep_row(self):
        el = Entry(self.sep_stream_window)
        el.grid(row=self.sep_row_num, column=0)
        ef = Entry(self.sep_stream_window)
        ef.grid(row=self.sep_row_num, column=1)
        self.el_ef_entry_list.append([el, ef])
        self.sep_row_num += 1


    def update_mixer_status_window(self):
        try:
            self.mixer_status_window.destroy()
        except:
            z=0
        self.mixer_status_window = Toplevel(self.def_window)
        Label(self.mixer_status_window, text='Defined Streams').grid(row=0, columnspan=2)
        row=1
        if 'in_streams' in self.entry_dict.keys():
            for st in self.entry_dict['in_streams'][9999]['stream']:
                text = ''
                for n in st['commodities']['item']:
                    text += n['commodity']
                    if n != st['commodities']['item'][-1]:
                        text += '\t'
                Button(self.mixer_status_window, text=text, command=lambda text=text:self.update_mix_stream(text)).grid(row=row, column=0)
                Button(self.mixer_status_window, text='x', command=lambda text=text:self.delete_mix_stream(text)).grid(row=row, column=1)
                row += 1

    def get_commodity_names_from_mix_stream(self, item_list):
        commodity_list = []
        for key in item_list:
            commodity_list.append(key['commodity'])
        return commodity_list


    def update_mix_stream(self, text):
        commodity_list = text.split()
        self.add_mix_stream()
        for indx, val in enumerate(self.entry_dict['in_streams'][9999]['stream']):
            if self.get_commodity_names_from_mix_stream(val['commodities']['item']) == commodity_list:
                it = indx
        self.mix_ratio_entry.insert(END, self.entry_dict['in_streams'][9999]['stream'][it]['info']['mixing_ratio'])
        self.buf_entry.insert(END, self.entry_dict['in_streams'][9999]['stream'][it]['info']['buf_size'])
        for indx, item in enumerate(self.entry_dict['in_streams'][9999]['stream'][it]['commodities']['item']):
            self.add_mix_row()
            self.commod_pref_entry_list[indx][0].insert(END, item['commodity']) 
            self.commod_pref_entry_list[indx][1].insert(END, item['pref'])
        del self.entry_dict['in_streams'][9999]['stream'][it]
    
    def delete_mix_stream(self, text):
        for indx, val in enumerate(self.entry_dict['in_streams'][9999]['stream']):
            if text.split() == self.get_commodity_names_from_mix_stream(val['commodities']['item']):
                kill = indx
        del self.entry_dict['in_streams'][9999]['stream'][kill]
        self.update_mixer_status_window()
        return

    def add_mix_stream(self):
        self.mix_stream_window = Toplevel(self.def_window)
        self.mix_stream_window.title('Mixture stream definition')
        Label(self.mix_stream_window, text='Mixing Ratio (<1.0)').grid(row=0, column=0)
        self.mix_ratio_entry = Entry(self.mix_stream_window)
        self.mix_ratio_entry.grid(row=0, column=1)
        Label(self.mix_stream_window, text='Buffer size').grid(row=1, column=0)
        self.buf_entry = Entry(self.mix_stream_window)
        self.buf_entry.grid(row=1, column=1)
        self.buf_entry.insert(END, '1e299')
        self.commod_pref_entry_list = []
        Button(self.mix_stream_window, text='Done', command=lambda:self.submit_mix_stream()).grid(row=0, column=2)

        Label(self.mix_stream_window, text='Commodities:').grid(row=2, columnspan=2)
        Button(self.mix_stream_window, text='Add commodity', command=lambda:self.add_mix_row()).grid(row=2, column=2)

        Label(self.mix_stream_window, text='Commodity').grid(row=3, column=0)
        Label(self.mix_stream_window, text='Preference').grid(row=3, column=1)
        self.mix_row_num = 4
        

    def submit_mix_stream(self):
        mix_stream_dict = {'info': {'mixing_ratio': self.mix_ratio_entry.get(),
                                    'buf_size': self.buf_entry.get()},
                           'commodities': {'item': []}}
        self.commod_pref_entry_list = [[x[0].get(), x[1].get()] for x in self.commod_pref_entry_list]
        for i in self.commod_pref_entry_list:
            if i[0] == i[1] == '':
                continue
            elif i[0] == '' or i[1] == '':
                messagebox.showerror('Error', 'Mix stream commodity or preference missing')
                return
            mix_stream_dict['commodities']['item'].append({'commodity': i[0], 'pref': i[1]})
        if len(mix_stream_dict['commodities']['item']) == 0:
            messagebox.showerror('Error', 'You did not define a single commodity')
            return  
        done = False
        for indx, val in enumerate(self.entry_dict['in_streams'][9999]['stream']):
            if mix_stream_dict['commodities']['item'] == val['commodities']['item']:
                set_indx = indx
                self.entry_dict['in_streams'][9999]['stream'][set_indx] = mix_stream_dict
                done = True
        if not done:
            self.entry_dict['in_streams'][9999]['stream'].append(mix_stream_dict)
        messagebox.showinfo('Success', 'Succesfully added mixture stream')
        self.mix_stream_window.destroy()
        self.update_mixer_status_window()


    def add_mix_row(self):
        commod = Entry(self.mix_stream_window)
        commod.grid(row=self.mix_row_num, column=0)
        pref = Entry(self.mix_stream_window)
        pref.grid(row=self.mix_row_num, column=1)
        self.commod_pref_entry_list.append([commod, pref])
        self.mix_row_num += 1
        


    def add_row(self, label, master, rownum, archetype):
        color = 'snow'
        if '*' in label:
            color = 'salmon1'
        if label == '':
            self.unknown_entry += 1
            label = self.unknown_entry
            self.entry_dict[label] = {rownum: [Entry(self.def_window), Entry(self.def_window)]}
            # input output
            self.entry_dict[label][rownum][0].grid(row=rownum, column=1)
            self.entry_dict[label][rownum][1].grid(row=rownum, column=3)
            self.start_row += 1
            return
        label = label.replace('*', '')
        q = Label(master, text=label, bg=color)
        q.grid(row=rownum, column=1)        
        CreateToolTip(q, text=self.generate_docstring(archetype, label))
        self.entry_dict[label] = {rownum: Entry(self.def_window)}
        if color == 'salmon1':
            default_val = str(self.j['annotations'][':'+archetype]['vars'][label]['default'])
            self.entry_dict[label][rownum].insert(END, default_val)
        self.entry_dict[label][rownum].grid(row=rownum, column=2)


    def generate_docstring(self, archetype, label):
        if not isinstance(self.type_dict[archetype][label], list):
            t = [self.type_dict[archetype][label]]
        else:
            t = self.type_dict[archetype][label]
        s = 'type= ' + ', '.join(t)
        if label in self.default_dict[archetype].keys():
            default = str(self.default_dict[archetype][label])
            if default == '':
                default = "''"
            s += '\n(default=%s)' %default
        s += '\n' + self.reasonable_linebreak(self.doc_dict[archetype][label])
        return s


    def reasonable_linebreak(self, string, lim=50):
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
                new_str += '\n'

        return new_str


    def add_row_oneormore(self, label, master, rownum, archetype):
        color = 'snow'
        if '*' in label:
            color = 'salmon1'
        if label == '':
            self.unknown_entry += 1
            label = self.unknown_entry * -1
            self.entry_dict[label] = {rownum: [Entry(self.def_window), Entry(self.def_window)]}
            self.entry_dict[label][rownum][0].grid(row=rownum, column=1)
            self.entry_dict[label][rownum][1].grid(row=rownum, column=2)
            Button(master, text='Add', command=lambda label=label, rownum=rownum: self.add_entry(label, rownum)).grid(row=rownum, column=0)
            self.start_row += 1
            return
        label = label.replace('*', '')
        q = Label(master, text=label, bg=color)
        q.grid(row=rownum, column=1)
        CreateToolTip(q, text=self.generate_docstring(archetype, label))
        self.entry_dict[label] = {rownum : []}
        self.entry_dict[label][rownum].append(Entry(self.def_window))
        self.entry_dict[label][rownum][-1].grid(row=rownum, column=2)
        Button(master, text='Add', command=lambda label=label, rownum=rownum: self.add_entry(label, rownum)).grid(row=rownum, column=0)


    def add_entry(self, label, rownum):
        # did you know that a negative sign messes up the isdigit
        if str(label).replace('-' ,'').isdigit():
            col = len(self.entry_dict[label][rownum]) + 1
        else:
            col = len(self.entry_dict[label][rownum]) + 2
        self.entry_dict[label][rownum].append(Entry(self.def_window))
        self.entry_dict[label][rownum][-1].grid(row=rownum, column=col)


    def guide(self):

        self.guide_window = Toplevel(self.master)
        self.guide_window.title('Facilities guide')
        self.guide_window.geometry('+0+400')
        guide_text = """
        Here you define archetypes with specific parameters to use in the simulation.
        An archetype is the code (general behavior of facility - e.g. reactor facility )
        A facility prototype is a facility archetype + user-defined parameters 
        (e.g. reactor with 3 60-assembly batches and 1000MWe power output).

        Here you can add facility prototypes by taking an archetype template and defining
        your parameters.

        Click on the dropdown to select the archetype you want to add, 
        and two windows will pop up. One is the documentation for the
        archetype and the parameters, and the other is the one you should
        fill out. The highlighted parameters have default values (specified in 
        documentation window), thus are optional. The parameters with 'Add'
        button next to it are parameters with (potentially) more than one
        variables. You can add more values by clicking 'Add'. Fill out
        the facility name and the parameters, then click 'Done' to
        save the facility. The window with 'Defined Archetypes' will update
        as you define facility prototypes. 

        """
        Label(self.guide_window, text=guide_text, justify=LEFT).pack(padx=30, pady=30)

