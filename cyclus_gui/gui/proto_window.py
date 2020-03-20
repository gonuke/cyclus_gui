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
from cyclus_gui.gui.window_tools import *
from cyclus_gui.gui.read_xml import *
from cyclus_gui.gui.hovertip import CreateToolTip

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
        self.screen_width = master.winfo_screenwidth()
        self.screen_height = master.winfo_screenheight()
        self.master.geometry('+0+%s' %int(self.screen_height/4))
        self.guide()
        Label(self.master, text='Choose a facility archetype to add:', bg='yellow').grid(row=0)
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
        self.region_status_window.geometry('+%s+0' %int(self.screen_width/3))
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
        self.status_window.geometry('+%s+0' %int(self.screen_width/4))
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
        self.def_window.geometry('+%s+%s' %(int(self.screen_width/4), int(self.screen_height/3)))
        Label(self.def_window, text='%s' %archetype, bg='lawn green').grid(row=0, columnspan=2)
        proto_name_entry = Entry(self.def_window)
        proto_name_entry.grid(row=1, column=1)
        proto_name_entry.insert(END, name)

        arche_long = self.arche_dict[name]
        Button(self.def_window, text='Done', command=lambda : self.submit_proto(arche_long, proto_name_entry.get())).grid(row=0, column=2)
        Label(self.def_window, text='Prototype Name:').grid(row=1, column=0)

        if arche_long in self.param_dict.keys():
            pprint(self.proto_dict[name]['config'][archetype])
            self.name = name
            # empty fillable entries
            self.def_entries(arche_long)
            
            # initializes values
            for param, val in self.proto_dict[name]['config'][archetype].items():
                if param in ['in_streams', 'streams']:
                    continue
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
            default_metadata = self.get_default_metadata()
            with open(path, 'w') as f:
                f.write(default_metadata)
            self.j = json.loads(default_metadata)


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
        self.def_window.geometry('+%s+%s' %(int(self.screen_width/7), int(self.screen_height/2.5)))
        archetype = self.tkvar.get()
        Label(self.def_window, text='%s' %archetype, bg='lawn green').grid(row=0, columnspan=2)

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
        print(self.entry_dict)
        for param, row_val_dict in self.entry_dict.items():
            if 'item' in row_val_dict.keys() or 'stream' in row_val_dict.keys():
                config_dict[archetype_name][param] = row_val_dict
                continue
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
                else:
                    val_list = val_list.get()
                    if val_list == '':
                        continue
                # check for empty values    
                config_dict[archetype_name][param] = val_list
        
        self.arche_dict[proto_name] = archetype
        self.proto_dict[proto_name] = {'archetype': archetype_name,
                                       'config': config_dict}
        pprint(self.proto_dict[proto_name])
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
        print('oneormore')
        print(oneormore)
        if 'streams' in oneormore:
            oneormore.remove('streams')
        if 'in_streams' in oneormore:
            oneormore.remove('in_streams')
        one = self.param_dict[archetype]['one']

        start_row += 1
        if archetype == 'cycamore:Separations':
            # special treatment for separations
            # add stream
            Label(self.def_window, text='Define Streams  ->->', bg='SteelBlue1').grid(row=start_row, column=1)
            Button(self.def_window, text='Add output Stream', command=lambda:self.add_sep_stream()).grid(row=start_row, column=2)
            self.entry_dict['streams'] = {'item': []}
            try:
                if 'streams' in self.proto_dict[self.name]['config'][archetype.split(':')[1]].keys():
                    self.entry_dict['streams']['item'] = self.proto_dict[self.name]['config'][archetype.split(':')[1]]['streams']['item']
            except:
                print('its not reopen')
            self.update_stream_status_window()

        if archetype == 'cycamore:Mixer':
            Label(self.def_window, text='Define Streams  ->->', bg='SteelBlue1').grid(row=start_row, column=1)
            Button(self.def_window, text='Add input Stream', command=lambda:self.add_mix_stream()).grid(row=start_row, column=2)
            self.entry_dict['in_streams'] = {'stream': []}
            try:
                if 'in_streams' in self.proto_dict[self.name]['config'][archetype.split(':')[1]].keys():
                    self.entry_dict['in_streams'] = {'stream': self.proto_dict[self.name]['config'][archetype.split(':')[1]]['in_streams']['stream']}
            except:
                print('its not reopen')
            self.update_mixer_status_window()

        for val in oneormore:
            start_row += 1
            self.add_row_oneormore(val, self.def_window, start_row, archetype)

        for val in one:
            start_row += 1
            self.add_row(val, self.def_window, start_row, archetype)   
            # add color for non-essential parameters




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
        self.stream_status_window.title('Defined Streams for Separations')
        self.stream_status_window.geometry('+0+%s' %int(self.screen_height/2))
        Label(self.stream_status_window, text='Defined Streams', bg='yellow').grid(row=0, columnspan=2)
        row=1
        if 'streams' in self.entry_dict.keys():
            t = self.make_a_list(self.entry_dict['streams']['item'])
            for st in t:
                Button(self.stream_status_window, text=st['commod'], command=lambda st=st:self.update_stream(st['commod'])).grid(row=row, column=0)
                Button(self.stream_status_window, text='x', command=lambda st=st:self.delete_stream(st['commod'])).grid(row=row, column=1)
                row += 1


    def update_stream(self, stream_name):
        self.add_sep_stream()
        t, notalist = self.make_a_list(self.entry_dict['streams']['item'], return_bool=True)
        for indx, val in enumerate(t):
            if stream_name == val['commod']:
                it = indx
        pprint(self.entry_dict['streams']['item'])
        print(it)
        self.commod_entry.insert(END, stream_name)
        if notalist:
            self.buf_entry.delete(0, END)
            self.buf_entry.insert(END, self.entry_dict['streams']['item']['info']['buf_size'])
            t = self.make_a_list(self.entry_dict['streams']['item']['info']['efficiencies']['item'])
            for indx2, item in enumerate(t):
                self.add_sep_row()
                self.el_ef_entry_list[indx2][0].insert(END, item['comp'])
                self.el_ef_entry_list[indx2][1].insert(END, item['eff'])

            # del self.entry_dict['streams']['item']

        else:
            self.buf_entry.delete(0, END)
            self.buf_entry.insert(END, self.entry_dict['streams']['item'][it]['info']['buf_size'])
            t = self.make_a_list(self.entry_dict['streams']['item'][it]['info']['efficiencies']['item'])
            for indx2, item in enumerate(t):
                self.add_sep_row()
                self.el_ef_entry_list[indx2][0].insert(END, item['comp'])
                self.el_ef_entry_list[indx2][1].insert(END, item['eff'])

            # del self.entry_dict['streams']['item'][it]


    def delete_stream(self, stream_name):
        w, notalist = self.make_a_list(self.entry_dict['streams']['item'], True)
        for indx, val in enumerate(w):
            if stream_name == val['commod']:
                kill = indx
        if notalist:
            del self.entry_dict['streams']['item']
        else:
            del self.entry_dict['streams']['item'][kill]
        self.update_stream_status_window()
        return


    def proto_guide_window(self, archetype):
        proto_guide_window_ = Toplevel(self.def_window)
        proto_guide_window_.title('%s documentation' %archetype)
        proto_guide_window_.geometry('+%s+%s' %(int(self.screen_width/1.5), int(self.screen_height/2)))
        string = '**The green highlighted parameters mean that they are essential.**\n'
        string += '**The non-highlighted parameters are optional**\n'
        string += '**Blue highlight parameters are special format.**\n'
        string += '**The parameters with `Add` button next to it can take in multiple values**\n'
        string += '**For descriptions of the parameters, hover your mouse over them!**\n'
        string += '**Your window has to be active for the mouse-over to work.**\n\n\n'
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
        self.sep_stream_window.geometry('+%s+%s' %(int(self.screen_width/3), int(self.screen_height/1.5)))
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
        print(self.entry_dict['streams'])
        t, notalist = self.make_a_list(self.entry_dict['streams']['item'], return_bool=True)
        for indx, val in enumerate(t):
            if val['commod'] == sep_stream_dict['commod']:
                set_indx = indx
                if notalist:
                    self.entry_dict['streams']['item'] = sep_stream_dict
                else:
                    self.entry_dict['streams']['item'][set_indx] = sep_stream_dict
                done = True
        if not done:
            if notalist:
                self.entry_dict['streams']['item'] = [self.entry_dict['streams']['item']]
            self.entry_dict['streams']['item'].append(sep_stream_dict)
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
        self.mixer_status_window.title('Defined Streams for Mixer')
        self.mixer_status_window.geometry('+0+%s' %int(self.screen_height/2))
        Label(self.mixer_status_window, text='Defined Streams', bg='yellow').grid(row=0, columnspan=2)
        row=1
        if 'in_streams' in self.entry_dict.keys():
            t = self.make_a_list(self.entry_dict['in_streams']['stream'])
            for st in t:
                text = '' 
                w = self.make_a_list(st['commodities']['item'])
                print(w)
                for n in w:
                    text += n['commodity']
                    if n != w[-1]:
                        text += '\t'
                disp_text = text + ' (%s)' %(st['info']['mixing_ratio'])
                Button(self.mixer_status_window, text=disp_text, anchor='w',
                       command=lambda text=text:self.update_mix_stream(text)).grid(row=row, column=0)
                Button(self.mixer_status_window, text='x', anchor='w',
                       command=lambda text=text:self.delete_mix_stream(text)).grid(row=row, column=1)
                row += 1

    def get_commodity_names_from_mix_stream(self, item_list):
        commodity_list = []
        w = self.make_a_list(item_list)
        for key in w:
            commodity_list.append(key['commodity'])
        return commodity_list


    def update_mix_stream(self, text):
        print(text)
        commodity_list = text.split()
        pprint(self.entry_dict)
        self.add_mix_stream()
        t, notalist = self.make_a_list(self.entry_dict['in_streams']['stream'], True)

        for indx, val in enumerate(t):
            print(self.get_commodity_names_from_mix_stream(val['commodities']['item']))
            print(commodity_list)
            if self.get_commodity_names_from_mix_stream(val['commodities']['item']) == commodity_list:
                it = indx

        if notalist:
            self.mix_ratio_entry.insert(END, self.entry_dict['in_streams']['stream']['info']['mixing_ratio'])
            self.buf_entry.delete(0, END)
            self.buf_entry.insert(END, self.entry_dict['in_streams']['stream']['info']['buf_size'])
            w = self.make_a_list(self.entry_dict['in_streams']['stream']['commodities']['item'])
            print(w)
            for indx2, item in enumerate(w):
                self.add_mix_row()
                self.commod_pref_entry_list[indx2][0].insert(END, item['commodity'])
                self.commod_pref_entry_list[indx2][1].insert(END, item['pref'])
            # self.entry_dict['in_streams']['stream'] = {}

        else:
            self.mix_ratio_entry.insert(END, self.entry_dict['in_streams']['stream'][it]['info']['mixing_ratio'])
            self.buf_entry.delete(0, END)
            self.buf_entry.insert(END, self.entry_dict['in_streams']['stream'][it]['info']['buf_size'])
            w = self.make_a_list(self.entry_dict['in_streams']['stream'][it]['commodities']['item'])
            for indx2, item in enumerate(w):
                self.add_mix_row()
                self.commod_pref_entry_list[indx2][0].insert(END, item['commodity']) 
                self.commod_pref_entry_list[indx2][1].insert(END, item['pref'])
        
            # del self.entry_dict['in_streams']['stream'][it]
    
    def delete_mix_stream(self, text):
        for indx, val in enumerate(self.entry_dict['in_streams']['stream']):
            if text.split() == self.get_commodity_names_from_mix_stream(val['commodities']['item']):
                kill = indx
        del self.entry_dict['in_streams']['stream'][kill]
        self.update_mixer_status_window()
        return

    def add_mix_stream(self):
        self.mix_stream_window = Toplevel(self.def_window)
        self.mix_stream_window.geometry('+%s+%s' %(int(self.screen_width/3), int(self.screen_height/1.5)))
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
        print(self.entry_dict)
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
        print('mix stream dict')
        pprint(mix_stream_dict)
        print('\nentry dict')
        pprint(self.entry_dict)
        t, notalist = self.make_a_list(self.entry_dict['in_streams']['stream'], True)
        print('t')
        print(t)
        for indx, val in enumerate(t):
            if mix_stream_dict['commodities']['item'] == val['commodities']['item']:
                set_indx = indx
                if notalist:
                    self.entry_dict['in_streams']['stream'] = mix_stream_dict
                else:
                    self.entry_dict['in_streams']['stream'][set_indx] = mix_stream_dict
                done = True
        if not done:
            if notalist:
                self.entry_dict['in_streams']['stream'] =[self.entry_dict['in_streams']['stream']]
            self.entry_dict['in_streams']['stream'].append(mix_stream_dict)
        messagebox.showinfo('Success', 'Succesfully added mixture stream.\nIf you were trying to update an existing stream, please delete the previous stream.')
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
        color = 'green yellow'
        if '*' in label:
            color = 'snow'
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
        if color == 'snow':
            default_val = str(self.j['annotations'][':'+archetype]['vars'][label]['default'])
            self.entry_dict[label][rownum].insert(END, default_val)
        self.entry_dict[label][rownum].grid(row=rownum, column=2)


    def generate_docstring(self, archetype, label):
        t = self.make_a_list(self.type_dict[archetype][label])
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
        if label == 'in_streams' or label=='stream':
            return 
        color = 'green yellow'
        if '*' in label:
            color = 'snow'
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
        try:
            CreateToolTip(q, text=self.generate_docstring(archetype, label))
        except: z=0
        self.entry_dict[label] = {rownum : []}
        self.entry_dict[label][rownum].append(Entry(self.def_window))
        self.entry_dict[label][rownum][-1].grid(row=rownum, column=2)
        Button(master, text='Add', command=lambda label=label, rownum=rownum: self.add_entry(label, rownum)).grid(row=rownum, column=0)

    def make_a_list(self, x, return_bool=False):
        if not isinstance(x, list):
            if return_bool:
                return [x], True
            else:
                return [x]
        else:
            if return_bool:
                return x, False
            else:
                return x

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
        self.guide_window.geometry('+%s+0' %int(self.screen_width/1.5))
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
fill out. The non-highlighted parameters have default values (specified in 
documentation window), thus are optional. The parameters with 'Add'
button next to it are parameters with (potentially) more than one
variables. You can add more values by clicking 'Add'. Fill out
the facility name and the parameters, then click 'Done' to
save the facility. The window with 'Defined Archetypes' will update
as you define facility prototypes.

You currently cannot edit two facilities simultaneously. 

        """
        st = ScrolledText(master=self.guide_window,
                          wrap=WORD)
        st.pack()
        st.insert(INSERT, guide_text)

    def get_default_metadata(self):
        return r"""{
         "annotations": {
          ":agents:KFacility": {
           "all_parents": [
            "cyclus::Agent", 
            "cyclus::Facility", 
            "cyclus::Ider", 
            "cyclus::StateWrangler", 
            "cyclus::TimeListener", 
            "cyclus::Trader"
           ], 
           "doc": "A facility designed for integration tests that both provides and consumes commodities. It changes its request and offer amounts based on a power law with respect to time.", 
           "entity": "facility", 
           "name": "cyclus::KFacility", 
           "parents": ["cyclus::Facility"], 
           "vars": {
            "current_capacity": {
             "alias": "current_capacity", 
             "default": 0, 
             "doc": "number of output commodity units that can be supplied at the current time step (infinite capacity can be represented by a very large number )", 
             "index": 5, 
             "shape": [-1], 
             "tooltip": "current output capacity", 
             "type": "double", 
             "uilabel": "Current Capacity"
            }, 
            "in_capacity": {
             "alias": "in_capacity", 
             "doc": "number of commodity units that can be taken at each timestep (infinite capacity can be represented by a very large number)", 
             "index": 3, 
             "shape": [-1], 
             "tooltip": "input commodity capacity", 
             "type": "double", 
             "uilabel": "Incoming Throughput"
            }, 
            "in_commod": {
             "alias": "in_commod", 
             "doc": "commodity that the k-facility consumes", 
             "index": 0, 
             "schematype": "token", 
             "shape": [-1], 
             "tooltip": "input commodity", 
             "type": "std::string", 
             "uilabel": "Input Commodity", 
             "uitype": "incommodity"
            }, 
            "inventory": {
             "alias": "inventory", 
             "capacity": "max_inv_size", 
             "index": 7, 
             "shape": [-1], 
             "tooltip": "inventory", 
             "type": "cyclus::toolkit::ResourceBuff", 
             "uilabel": "inventory"
            }, 
            "k_factor_in": {
             "alias": "k_factor_in", 
             "doc": "conversion factor that governs the behavior of the k-facility's input commodity capacity", 
             "index": 8, 
             "shape": [-1], 
             "tooltip": "input k-factor", 
             "type": "double", 
             "uilabel": "Input K-Factor"
            }, 
            "k_factor_out": {
             "alias": "k_factor_out", 
             "doc": "conversion factor that governs the behavior of the k-facility's output commodity capacity", 
             "index": 9, 
             "shape": [-1], 
             "tooltip": "output k-factor", 
             "type": "double", 
             "uilabel": "Output K-Factor"
            }, 
            "max_inv_size": {
             "alias": "max_inv_size", 
             "default": 1.000000000000000e+299, 
             "doc": "total maximum inventory size of the k-facility", 
             "index": 6, 
             "shape": [-1], 
             "tooltip": "k-facility maximum inventory size", 
             "type": "double", 
             "uilabel": "Maximum Inventory"
            }, 
            "out_capacity": {
             "alias": "out_capacity", 
             "doc": "number of commodity units that can be supplied at each timestep (infinite capacity can be represented by a very large number)", 
             "index": 4, 
             "shape": [-1], 
             "tooltip": "output commodity capacity", 
             "type": "double", 
             "uilabel": "Outgoing Throughput"
            }, 
            "out_commod": {
             "alias": "out_commod", 
             "doc": "commodity that the k-facility supplies", 
             "index": 2, 
             "schematype": "token", 
             "shape": [-1], 
             "tooltip": "output commodity", 
             "type": "std::string", 
             "uilabel": "Output Commodity", 
             "uitype": "outcommodity"
            }, 
            "recipe_name": {
             "alias": "recipe_name", 
             "doc": "recipe name for the k-facility's in-commodity", 
             "index": 1, 
             "schematype": "token", 
             "shape": [50], 
             "tooltip": "in-commodity recipe name", 
             "type": "std::string", 
             "uilabel": "Input Recipe", 
             "uitype": "recipe"
            }
           }
          }, 
          ":agents:NullInst": {
           "all_parents": [
            "cyclus::Agent", 
            "cyclus::Ider", 
            "cyclus::Institution", 
            "cyclus::StateWrangler", 
            "cyclus::TimeListener"
           ], 
           "doc": "An instition that owns facilities in the simulation but exhibits null behavior. No parameters are given when using the null institution.", 
           "entity": "institution", 
           "name": "cyclus::NullInst", 
           "parents": ["cyclus::Institution"], 
           "vars": {}
          }, 
          ":agents:NullRegion": {
           "all_parents": [
            "cyclus::Agent", 
            "cyclus::Ider", 
            "cyclus::Region", 
            "cyclus::StateWrangler", 
            "cyclus::TimeListener"
           ], 
           "doc": "A region that owns the simulation's institutions but exhibits null behavior. No parameters are given when using the null region.", 
           "entity": "region", 
           "name": "cyclus::NullRegion", 
           "parents": ["cyclus::Region"], 
           "vars": {}
          }, 
          ":agents:Sink": {
           "all_parents": [
            "cyclus::Agent", 
            "cyclus::Facility", 
            "cyclus::Ider", 
            "cyclus::StateWrangler", 
            "cyclus::TimeListener", 
            "cyclus::Trader"
           ], 
           "doc": "A minimum implementation sink facility that accepts specified amounts of commodities from other agents", 
           "entity": "facility", 
           "name": "cyclus::Sink", 
           "parents": ["cyclus::Facility"], 
           "vars": {
            "capacity": {
             "alias": "capacity", 
             "doc": "capacity the sink facility can accept at each time step", 
             "index": 3, 
             "range": [0.0, 1.000000000000000e+299], 
             "shape": [-1], 
             "tooltip": "sink capacity", 
             "type": "double", 
             "uilabel": "Maximum Throughput", 
             "uitype": "range"
            }, 
            "in_commods": {
             "alias": ["in_commods", "val"], 
             "doc": "commodities that the sink facility accepts ", 
             "index": 0, 
             "shape": [-1, -1], 
             "tooltip": ["input commodities for the sink", ""], 
             "type": ["std::vector", "std::string"], 
             "uilabel": ["List of Input Commodities", ""], 
             "uitype": ["oneormore", "incommodity"]
            }, 
            "inventory": {
             "alias": "inventory", 
             "capacity": "max_inv_size", 
             "index": 4, 
             "shape": [-1], 
             "tooltip": "inventory", 
             "type": "cyclus::toolkit::ResourceBuff", 
             "uilabel": "inventory"
            }, 
            "max_inv_size": {
             "alias": "max_inv_size", 
             "default": 1.000000000000000e+299, 
             "doc": "total maximum inventory size of sink facility", 
             "index": 2, 
             "shape": [-1], 
             "tooltip": "sink maximum inventory size", 
             "type": "double", 
             "uilabel": "Maximum Inventory"
            }, 
            "recipe_name": {
             "alias": "recipe_name", 
             "default": "", 
             "doc": "Name of recipe to request.If empty, sink requests material no particular composition.", 
             "index": 1, 
             "shape": [-1], 
             "tooltip": "input/request recipe name", 
             "type": "std::string", 
             "uilabel": "Input Recipe", 
             "uitype": "recipe"
            }
           }
          }, 
          ":agents:Source": {
           "all_parents": [
            "cyclus::Agent", 
            "cyclus::Facility", 
            "cyclus::Ider", 
            "cyclus::StateWrangler", 
            "cyclus::TimeListener", 
            "cyclus::Trader"
           ], 
           "doc": "A minimum implementation source facility that provides a commodity with a given capacity", 
           "entity": "facility", 
           "name": "cyclus::Source", 
           "parents": ["cyclus::Facility"], 
           "vars": {
            "capacity": {
             "alias": "capacity", 
             "doc": "amount of commodity that can be supplied at each time step", 
             "index": 2, 
             "range": [0.0, 1.000000000000000e+299], 
             "shape": [-1], 
             "tooltip": "source capacity", 
             "type": "double", 
             "uilabel": "Maximum Throughput", 
             "uitype": "range"
            }, 
            "commod": {
             "alias": "commod", 
             "doc": "commodity that the source facility supplies", 
             "index": 0, 
             "schematype": "token", 
             "shape": [-1], 
             "tooltip": "source commodity", 
             "type": "std::string", 
             "uilabel": "Commodity", 
             "uitype": "outcommodity"
            }, 
            "recipe_name": {
             "alias": "recipe_name", 
             "default": "", 
             "doc": "Recipe name for source facility's commodity.If empty, source supplies material with requested compositions.", 
             "index": 1, 
             "schematype": "token", 
             "shape": [-1], 
             "tooltip": "commodity recipe name", 
             "type": "std::string", 
             "uilabel": "Recipe", 
             "uitype": "recipe"
            }
           }
          }, 
          ":cycamore:DeployInst": {
           "all_parents": [
            "cyclus::Agent", 
            "cyclus::Ider", 
            "cyclus::Institution", 
            "cyclus::StateWrangler", 
            "cyclus::TimeListener", 
            "cyclus::toolkit::Position"
           ], 
           "doc": "Builds and manages agents (facilities) according to a manually specified deployment schedule. Deployed agents are automatically decommissioned at the end of their lifetime.  The user specifies a list of prototypes for each and corresponding build times, number to build, and (optionally) lifetimes.  The same prototype can be specified multiple times with any combination of the same or different build times, build number, and lifetimes. ", 
           "entity": "institution", 
           "name": "cycamore::DeployInst", 
           "parents": ["cyclus::Institution", "cyclus::toolkit::Position"], 
           "vars": {
            "build_times": {
             "alias": ["build_times", "val"], 
             "doc": "Time step on which to deploy agents given in prototype list (same order).", 
             "index": 1, 
             "shape": [-1, -1], 
             "tooltip": ["build_times", ""], 
             "type": ["std::vector", "int"], 
             "uilabel": ["Deployment times", ""]
            }, 
            "latitude": {
             "alias": "latitude", 
             "default": 0.0, 
             "doc": "Latitude of the agent's geographical position. The value should be expressed in degrees as a double.", 
             "index": 4, 
             "shape": [-1], 
             "tooltip": "latitude", 
             "type": "double", 
             "uilabel": "Geographical latitude in degrees as a double"
            }, 
            "lifetimes": {
             "alias": ["lifetimes", "val"], 
             "default": [], 
             "doc": "Lifetimes for each prototype in prototype list (same order). These lifetimes override the lifetimes in the original prototype definition. If unspecified, lifetimes from the original prototype definitions are used. Although a new prototype is created in the Prototypes table for each lifetime with the suffix '_life_[lifetime]', all deployed agents themselves will have the same original prototype name (and so will the Agents tables).", 
             "index": 3, 
             "shape": [-1, -1], 
             "tooltip": ["lifetimes", ""], 
             "type": ["std::vector", "int"], 
             "uilabel": ["Lifetimes", ""]
            }, 
            "longitude": {
             "alias": "longitude", 
             "default": 0.0, 
             "doc": "Longitude of the agent's geographical position. The value should be expressed in degrees as a double.", 
             "index": 5, 
             "shape": [-1], 
             "tooltip": "longitude", 
             "type": "double", 
             "uilabel": "Geographical longitude in degrees as a double"
            }, 
            "n_build": {
             "alias": ["n_build", "val"], 
             "doc": "Number of each prototype given in prototype list that should be deployed (same order).", 
             "index": 2, 
             "shape": [-1, -1], 
             "tooltip": ["n_build", ""], 
             "type": ["std::vector", "int"], 
             "uilabel": ["Number to deploy", ""]
            }, 
            "prototypes": {
             "alias": ["prototypes", "val"], 
             "doc": "Ordered list of prototypes to build.", 
             "index": 0, 
             "shape": [-1, -1], 
             "tooltip": ["prototypes", ""], 
             "type": ["std::vector", "std::string"], 
             "uilabel": ["Prototypes to deploy", ""], 
             "uitype": ["oneormore", "prototype"]
            }
           }
          }, 
          ":cycamore:Enrichment": {
           "all_parents": [
            "cyclus::Agent", 
            "cyclus::Facility", 
            "cyclus::Ider", 
            "cyclus::StateWrangler", 
            "cyclus::TimeListener", 
            "cyclus::Trader", 
            "cyclus::toolkit::Position"
           ], 
           "doc": "The Enrichment facility is a simple agent that enriches natural uranium in a Cyclus simulation. It does not explicitly compute the physical enrichment process, rather it calculates the SWU required to convert an source uranium recipe (i.e. natural uranium) into a requested enriched recipe (i.e. 4 per cent enriched uranium), given the natural uranium inventory constraint and its SWU capacity constraint.\n\nThe Enrichment facility requests an input commodity and associated recipe whose quantity is its remaining inventory capacity.  All facilities trading the same input commodity (even with different recipes) will offer materials for trade.  The Enrichment facility accepts any input materials with enrichments less than its tails assay, as long as some U235 is present, and preference increases with U235 content.  If no U235 is present in the offered material, the trade preference is set to -1 and the material is not accepted.  Any material components other than U235 and U238 are sent directly to the tails buffer.\n\nThe Enrichment facility will bid on any request for its output commodity up to the maximum allowed enrichment (if not specified, default is 100 percent) It bids on either the request quantity, or the maximum quanity allowed by its SWU constraint or natural uranium inventory, whichever is lower. If multiple output commodities with different enrichment levels are requested and the facility does not have the SWU or quantity capacity to meet all requests, the requests are fully, then partially filled in unspecified but repeatable order.\n\nAccumulated tails inventory is offered for trading as a specifiable output commodity.", 
           "entity": "facility", 
           "name": "cycamore::Enrichment", 
           "niche": "enrichment facility", 
           "parents": ["cyclus::Facility", "cyclus::toolkit::Position"], 
           "vars": {
            "feed_commod": {
             "alias": "feed_commod", 
             "doc": "feed commodity that the enrichment facility accepts", 
             "index": 0, 
             "shape": [-1], 
             "tooltip": "feed commodity", 
             "type": "std::string", 
             "uilabel": "Feed Commodity", 
             "uitype": "incommodity"
            }, 
            "feed_recipe": {
             "alias": "feed_recipe", 
             "doc": "recipe for enrichment facility feed commodity", 
             "index": 1, 
             "shape": [-1], 
             "tooltip": "feed recipe", 
             "type": "std::string", 
             "uilabel": "Feed Recipe", 
             "uitype": "inrecipe"
            }, 
            "initial_feed": {
             "alias": "initial_feed", 
             "default": 0, 
             "doc": "amount of natural uranium stored at the enrichment facility at the beginning of the simulation (kg)", 
             "index": 5, 
             "shape": [-1], 
             "tooltip": "initial uranium reserves (kg)", 
             "type": "double", 
             "uilabel": "Initial Feed Inventory"
            }, 
            "inventory": {
             "capacity": "max_feed_inventory", 
             "index": 9, 
             "shape": [-1, -1], 
             "type": ["cyclus::toolkit::ResBuf", "cyclus::Material"]
            }, 
            "latitude": {
             "alias": "latitude", 
             "default": 0.0, 
             "doc": "Latitude of the agent's geographical position. The value should be expressed in degrees as a double.", 
             "index": 11, 
             "shape": [-1], 
             "tooltip": "latitude", 
             "type": "double", 
             "uilabel": "Geographical latitude in degrees as a double"
            }, 
            "longitude": {
             "alias": "longitude", 
             "default": 0.0, 
             "doc": "Longitude of the agent's geographical position. The value should be expressed in degrees as a double.", 
             "index": 12, 
             "shape": [-1], 
             "tooltip": "longitude", 
             "type": "double", 
             "uilabel": "Geographical longitude in degrees as a double"
            }, 
            "max_enrich": {
             "alias": "max_enrich", 
             "default": 1.0, 
             "doc": "maximum allowed weight fraction of U235 in product", 
             "index": 7, 
             "range": [0.0, 1.0], 
             "schema": "<optional>          <element name=\"max_enrich\">              <data type=\"double\">                  <param name=\"minInclusive\">0</param>                  <param name=\"maxInclusive\">1</param>              </data>          </element>      </optional>", 
             "shape": [-1], 
             "tooltip": "maximum allowed enrichment fraction", 
             "type": "double", 
             "uilabel": "Maximum Allowed Enrichment", 
             "uitype": "range"
            }, 
            "max_feed_inventory": {
             "alias": "max_feed_inventory", 
             "default": 1.000000000000000e+299, 
             "doc": "maximum total inventory of natural uranium in the enrichment facility (kg)", 
             "index": 6, 
             "range": [0.0, 1.000000000000000e+299], 
             "shape": [-1], 
             "tooltip": "max inventory of feed material (kg)", 
             "type": "double", 
             "uilabel": "Maximum Feed Inventory", 
             "uitype": "range"
            }, 
            "product_commod": {
             "alias": "product_commod", 
             "doc": "product commodity that the enrichment facility generates", 
             "index": 2, 
             "shape": [-1], 
             "tooltip": "product commodity", 
             "type": "std::string", 
             "uilabel": "Product Commodity", 
             "uitype": "outcommodity"
            }, 
            "swu_capacity": {
             "alias": "swu_capacity", 
             "default": 1.000000000000000e+299, 
             "doc": "separative work unit (SWU) capacity of enrichment facility (kgSWU/timestep) ", 
             "index": 8, 
             "range": [0.0, 1.000000000000000e+299], 
             "shape": [-1], 
             "tooltip": "SWU capacity (kgSWU/month)", 
             "type": "double", 
             "uilabel": "SWU Capacity", 
             "uitype": "range"
            }, 
            "tails": {
             "index": 10, 
             "shape": [-1, -1], 
             "type": ["cyclus::toolkit::ResBuf", "cyclus::Material"]
            }, 
            "tails_assay": {
             "alias": "tails_assay", 
             "default": 0.0030, 
             "doc": "tails assay from the enrichment process", 
             "index": 4, 
             "range": [0.0, 0.0030], 
             "shape": [-1], 
             "tooltip": "tails assay", 
             "type": "double", 
             "uilabel": "Tails Assay", 
             "uitype": "range"
            }, 
            "tails_commod": {
             "alias": "tails_commod", 
             "doc": "tails commodity supplied by enrichment facility", 
             "index": 3, 
             "shape": [-1], 
             "tooltip": "tails commodity", 
             "type": "std::string", 
             "uilabel": "Tails Commodity", 
             "uitype": "outcommodity"
            }
           }
          }, 
          ":cycamore:FuelFab": {
           "all_parents": [
            "cyclus::Agent", 
            "cyclus::Facility", 
            "cyclus::Ider", 
            "cyclus::StateWrangler", 
            "cyclus::TimeListener", 
            "cyclus::Trader", 
            "cyclus::toolkit::Position"
           ], 
           "doc": "FuelFab takes in 2 streams of material and mixes them in ratios in order to supply material that matches some neutronics properties of reqeusted material.  It uses an equivalence type method [1] inspired by a similar approach in the COSI fuel cycle simulator.\n\nThe FuelFab has 3 input inventories: fissile stream, filler stream, and an optional top-up inventory.  All materials received into each inventory are always combined into a single material (i.e. a single fissile material, a single filler material, etc.).  The input streams and requested fuel composition are each assigned weights based on summing:\n\n    N * (p_i - p_U238) / (p_Pu239 - p_U238)\n\nfor each nuclide where:\n\n    - p = nu*sigma_f - sigma_a   for the nuclide\n    - p_U238 is p for pure U238\n    - p_Pu239 is p for pure Pu239\n    - N is the nuclide's atom fraction\n    - nu is the average # neutrons per fission\n    - sigma_f is the microscopic fission cross-section\n    - sigma_a is the microscopic neutron absorption cross-section\n\nThe cross sections are from the simple cross section library in PyNE. They can be set to either a thermal or fast neutron spectrum.  A linear interpolation is performed using the weights of the fissile, filler, and target streams. The interpolation is used to compute a mixing ratio of the input streams that matches the target weight.  In the event that the target weight is higher than the fissile stream weight, the FuelFab will attempt to use the top-up and fissile input streams together instead of the fissile and filler streams.  All supplied material will always have the same weight as the requested material.\n\nThe supplying of mixed material is constrained by available inventory quantities and a per time step throughput limit.  Requests for fuel material larger than the throughput can never be met.  Fissile inventory can be requested/received via one or more commodities.  The DRE request preference for each of these commodities can also optionally be specified. By default, the top-up inventory size is zero, and it is not used for mixing. \n\n[1] Baker, A. R., and R. W. Ross. \"Comparison of the value of plutonium and    uranium isotopes in fast reactors.\" Proceedings of the Conference on    Breeding. Economics, and Safety in Large Fast Power Reactors. 1963.", 
           "entity": "facility", 
           "name": "cycamore::FuelFab", 
           "niche": "fabrication", 
           "parents": ["cyclus::Facility", "cyclus::toolkit::Position"], 
           "vars": {
            "fill": {
             "capacity": "fill_size", 
             "index": 4, 
             "shape": [-1, -1], 
             "type": ["cyclus::toolkit::ResBuf", "cyclus::Material"]
            }, 
            "fill_commod_prefs": {
             "alias": ["fill_commod_prefs", "val"], 
             "default": [], 
             "doc": "Filler stream commodity request preferences for each of the given filler commodities (same order). If unspecified, default is to use 1.0 for all preferences.", 
             "index": 1, 
             "shape": [-1, -1], 
             "tooltip": ["fill_commod_prefs", ""], 
             "type": ["std::vector", "double"], 
             "uilabel": ["Filler Stream Preferences", ""]
            }, 
            "fill_commods": {
             "alias": ["fill_commods", "val"], 
             "doc": "Ordered list of commodities on which to requesting filler stream material.", 
             "index": 0, 
             "shape": [-1, -1], 
             "tooltip": ["fill_commods", ""], 
             "type": ["std::vector", "std::string"], 
             "uilabel": ["Filler Stream Commodities", ""], 
             "uitype": ["oneormore", "incommodity"]
            }, 
            "fill_recipe": {
             "alias": "fill_recipe", 
             "doc": "Name of recipe to be used in filler material stream requests.", 
             "index": 2, 
             "shape": [-1], 
             "tooltip": "fill_recipe", 
             "type": "std::string", 
             "uilabel": "Filler Stream Recipe", 
             "uitype": "inrecipe"
            }, 
            "fill_size": {
             "alias": "fill_size", 
             "doc": "Size of filler material stream inventory.", 
             "index": 3, 
             "shape": [-1], 
             "tooltip": "fill_size", 
             "type": "double", 
             "uilabel": "Filler Stream Inventory Capacity", 
             "units": "kg"
            }, 
            "fiss": {
             "capacity": "fiss_size", 
             "index": 9, 
             "shape": [-1, -1], 
             "type": ["cyclus::toolkit::ResBuf", "cyclus::Material"]
            }, 
            "fiss_commod_prefs": {
             "alias": ["fiss_commod_prefs", "val"], 
             "default": [], 
             "doc": "Fissile stream commodity request preferences for each of the given fissile commodities (same order). If unspecified, default is to use 1.0 for all preferences.", 
             "index": 6, 
             "shape": [-1, -1], 
             "tooltip": ["fiss_commod_prefs", ""], 
             "type": ["std::vector", "double"], 
             "uilabel": ["Fissile Stream Preferences", ""]
            }, 
            "fiss_commods": {
             "alias": ["fiss_commods", "val"], 
             "doc": "Ordered list of commodities on which to requesting fissile stream material.", 
             "index": 5, 
             "shape": [-1, -1], 
             "tooltip": ["fiss_commods", ""], 
             "type": ["std::vector", "std::string"], 
             "uilabel": ["Fissile Stream Commodities", ""], 
             "uitype": ["oneormore", "incommodity"]
            }, 
            "fiss_recipe": {
             "alias": "fiss_recipe", 
             "default": "", 
             "doc": "Name for recipe to be used in fissile stream requests. Empty string results in use of an empty dummy recipe.", 
             "index": 7, 
             "shape": [-1], 
             "tooltip": "fiss_recipe", 
             "type": "std::string", 
             "uilabel": "Fissile Stream Recipe", 
             "uitype": "inrecipe"
            }, 
            "fiss_size": {
             "alias": "fiss_size", 
             "doc": "Size of fissile material stream inventory.", 
             "index": 8, 
             "shape": [-1], 
             "tooltip": "fiss_size", 
             "type": "double", 
             "uilabel": "Fissile Stream Inventory Capacity", 
             "units": "kg"
            }, 
            "latitude": {
             "alias": "latitude", 
             "default": 0.0, 
             "doc": "Latitude of the agent's geographical position. The value should be expressed in degrees as a double.", 
             "index": 18, 
             "shape": [-1], 
             "tooltip": "latitude", 
             "type": "double", 
             "uilabel": "Geographical latitude in degrees as a double"
            }, 
            "longitude": {
             "alias": "longitude", 
             "default": 0.0, 
             "doc": "Longitude of the agent's geographical position. The value should be expressed in degrees as a double.", 
             "index": 19, 
             "shape": [-1], 
             "tooltip": "longitude", 
             "type": "double", 
             "uilabel": "Geographical longitude in degrees as a double"
            }, 
            "outcommod": {
             "alias": "outcommod", 
             "doc": "Commodity on which to offer/supply mixed fuel material.", 
             "index": 15, 
             "shape": [-1], 
             "tooltip": "outcommod", 
             "type": "std::string", 
             "uilabel": "Output Commodity", 
             "uitype": "outcommodity"
            }, 
            "spectrum": {
             "alias": "spectrum", 
             "categorical": ["fission_spectrum_ave", "thermal"], 
             "doc": "The type of cross-sections to use for composition property calculation. Use 'fission_spectrum_ave' for fast reactor compositions or 'thermal' for thermal reactors.", 
             "index": 17, 
             "shape": [-1], 
             "tooltip": "spectrum", 
             "type": "std::string", 
             "uilabel": "Spectrum type", 
             "uitype": "combobox"
            }, 
            "throughput": {
             "alias": "throughput", 
             "default": 1.000000000000000e+299, 
             "doc": "Maximum number of kg of fuel material that can be supplied per time step.", 
             "index": 16, 
             "range": [0.0, 1.000000000000000e+299], 
             "shape": [-1], 
             "tooltip": "throughput", 
             "type": "double", 
             "uilabel": "Maximum Throughput", 
             "uitype": "range", 
             "units": "kg"
            }, 
            "topup": {
             "capacity": "topup_size", 
             "index": 14, 
             "shape": [-1, -1], 
             "type": ["cyclus::toolkit::ResBuf", "cyclus::Material"]
            }, 
            "topup_commod": {
             "alias": "topup_commod", 
             "default": "", 
             "doc": "Commodity on which to request material for top-up stream. This MUST be set if 'topup_size > 0'.", 
             "index": 10, 
             "shape": [-1], 
             "tooltip": "topup_commod", 
             "type": "std::string", 
             "uilabel": "Top-up Stream Commodity", 
             "uitype": "incommodity"
            }, 
            "topup_pref": {
             "alias": "topup_pref", 
             "default": 1.0, 
             "doc": "Top-up material stream request preference.", 
             "index": 11, 
             "shape": [-1], 
             "tooltip": "topup_pref", 
             "type": "double", 
             "uilabel": "Top-up Stream Preference"
            }, 
            "topup_recipe": {
             "alias": "topup_recipe", 
             "default": "", 
             "doc": "Name of recipe to be used in top-up material stream requests. This MUST be set if 'topup_size > 0'.", 
             "index": 12, 
             "shape": [-1], 
             "tooltip": "topup_recipe", 
             "type": "std::string", 
             "uilabel": "Top-up Stream Recipe", 
             "uitype": "inrecipe"
            }, 
            "topup_size": {
             "alias": "topup_size", 
             "default": 0, 
             "doc": "Size of top-up material stream inventory.", 
             "index": 13, 
             "shape": [-1], 
             "tooltip": "topup_size", 
             "type": "double", 
             "uilabel": "Top-up Stream Inventory Capacity", 
             "units": "kg"
            }
           }
          }, 
          ":cycamore:GrowthRegion": {
           "all_parents": [
            "cyclus::Agent", 
            "cyclus::Ider", 
            "cyclus::Region", 
            "cyclus::StateWrangler", 
            "cyclus::TimeListener", 
            "cyclus::toolkit::Position"
           ], 
           "doc": "A region that governs a scenario in which there is growth in demand for a commodity. ", 
           "entity": "region", 
           "name": "cycamore::GrowthRegion", 
           "parents": ["cyclus::Region", "cyclus::toolkit::Position"], 
           "vars": {
            "commodity_demand": {
             "alias": [
              ["growth", "item"], 
              "commod", 
              ["piecewise_function", ["piece", "start", ["function", "type", "params"]]]
             ], 
             "doc": "Nameplate capacity demand functions.\n\nEach demand type must be for a commodity for which capacity can be built (e.g., 'power' from cycamore::Reactors). Any archetype that implements the cyclus::toolkit::CommodityProducer interface can interact with the GrowthRegion in the manner.\n\nDemand functions are defined as piecewise functions. Each piece must be provided a starting time and function description. Each function description is comprised of a function type and associated parameters. \n\n  * Start times are inclusive. For a start time :math:`t_0`, the demand function is evaluated on :math:`[t_0, \\infty)`.\n\n  * Supported function types are based on the `cyclus::toolkit::BasicFunctionFactory types <http://fuelcycle.org/cyclus/api/classcyclus_1_1toolkit_1_1BasicFunctionFactory.html#a2f3806305d99a745ab57c300e54a603d>`_. \n\n  * The type name is the lower-case name of the function (e.g., 'linear', 'exponential', etc.).\n\n  * The parameters associated with each function type can be found on their respective documentation pages.", 
             "index": 0, 
             "shape": [-1, -1, -1, -1, -1, -1, -1, -1], 
             "tooltip": [["commodity_demand", ""], "", ["", ["", "", ["", "", ""]]]], 
             "type": [
              "std::map", 
              "std::string", 
              [
               "std::vector", 
               ["std::pair", "int", ["std::pair", "std::string", "std::string"]]
              ]
             ], 
             "uilabel": [["Growth Demand Curves", ""], "", ["", ["", "", ["", "", ""]]]], 
             "uitype": [
              "oneormore", 
              "string", 
              ["oneormore", ["pair", "int", ["pair", "string", "string"]]]
             ]
            }, 
            "growth": "commodity_demand", 
            "latitude": {
             "alias": "latitude", 
             "default": 0.0, 
             "doc": "Latitude of the agent's geographical position. The value should be expressed in degrees as a double.", 
             "index": 2, 
             "shape": [-1], 
             "tooltip": "latitude", 
             "type": "double", 
             "uilabel": "Geographical latitude in degrees as a double"
            }, 
            "longitude": {
             "alias": "longitude", 
             "default": 0.0, 
             "doc": "Longitude of the agent's geographical position. The value should be expressed in degrees as a double.", 
             "index": 3, 
             "shape": [-1], 
             "tooltip": "longitude", 
             "type": "double", 
             "uilabel": "Geographical longitude in degrees as a double"
            }
           }
          }, 
          ":cycamore:ManagerInst": {
           "all_parents": [
            "cyclus::Agent", 
            "cyclus::Ider", 
            "cyclus::Institution", 
            "cyclus::StateWrangler", 
            "cyclus::TimeListener", 
            "cyclus::toolkit::AgentManaged", 
            "cyclus::toolkit::Builder", 
            "cyclus::toolkit::CommodityProducerManager", 
            "cyclus::toolkit::Position"
           ], 
           "doc": "An institution that owns and operates a manually entered list of facilities in the input file", 
           "entity": "institution", 
           "name": "cycamore::ManagerInst", 
           "parents": [
            "cyclus::Institution", 
            "cyclus::toolkit::Builder", 
            "cyclus::toolkit::CommodityProducerManager", 
            "cyclus::toolkit::Position"
           ], 
           "vars": {
            "latitude": {
             "alias": "latitude", 
             "default": 0.0, 
             "doc": "Latitude of the agent's geographical position. The value should be expressed in degrees as a double.", 
             "index": 1, 
             "shape": [-1], 
             "tooltip": "latitude", 
             "type": "double", 
             "uilabel": "Geographical latitude in degrees as a double"
            }, 
            "longitude": {
             "alias": "longitude", 
             "default": 0.0, 
             "doc": "Longitude of the agent's geographical position. The value should be expressed in degrees as a double.", 
             "index": 2, 
             "shape": [-1], 
             "tooltip": "longitude", 
             "type": "double", 
             "uilabel": "Geographical longitude in degrees as a double"
            }, 
            "prototypes": {
             "alias": ["prototypes", "val"], 
             "doc": "A set of facility prototypes that this institution can build. All prototypes in this list must be based on an archetype that implements the cyclus::toolkit::CommodityProducer interface", 
             "index": 0, 
             "shape": [-1, -1], 
             "tooltip": ["producer facility prototypes", ""], 
             "type": ["std::vector", "std::string"], 
             "uilabel": ["Producer Prototype List", ""], 
             "uitype": ["oneormore", "prototype"]
            }
           }
          }, 
          ":cycamore:Mixer": {
           "all_parents": [
            "cyclus::Agent", 
            "cyclus::Facility", 
            "cyclus::Ider", 
            "cyclus::StateWrangler", 
            "cyclus::TimeListener", 
            "cyclus::Trader", 
            "cyclus::toolkit::Position"
           ], 
           "doc": "Mixer mixes N streams with fixed, static, user-specified ratios into a single output stream. The Mixer has N input inventories: one for each streams to be mixed, and one output stream. The supplying of mixed material is constrained by  available inventory of mixed material quantities.", 
           "entity": "facility", 
           "name": "cycamore::Mixer", 
           "niche": "mixing facility", 
           "parents": ["cyclus::Facility", "cyclus::toolkit::Position"], 
           "vars": {
            "in_streams": "streams_", 
            "latitude": {
             "alias": "latitude", 
             "default": 0.0, 
             "doc": "Latitude of the agent's geographical position. The value should be expressed in degrees as a double.", 
             "index": 6, 
             "shape": [-1], 
             "tooltip": "latitude", 
             "type": "double", 
             "uilabel": "Geographical latitude in degrees as a double"
            }, 
            "longitude": {
             "alias": "longitude", 
             "default": 0.0, 
             "doc": "Longitude of the agent's geographical position. The value should be expressed in degrees as a double.", 
             "index": 7, 
             "shape": [-1], 
             "tooltip": "longitude", 
             "type": "double", 
             "uilabel": "Geographical longitude in degrees as a double"
            }, 
            "out_buf_size": {
             "alias": "out_buf_size", 
             "default": 1.000000000000000e+299, 
             "doc": "Maximum amount of mixed material that can be stored. If full, the facility halts operation until space becomes available.", 
             "index": 3, 
             "range": [0.0, 1.000000000000000e+299], 
             "shape": [-1], 
             "tooltip": "out_buf_size", 
             "type": "double", 
             "uilabel": "Maximum Leftover Inventory", 
             "uitype": "range", 
             "units": "kg"
            }, 
            "out_commod": {
             "alias": "out_commod", 
             "doc": "Commodity on which to offer/supply mixed fuel material.", 
             "index": 2, 
             "shape": [-1], 
             "tooltip": "out_commod", 
             "type": "std::string", 
             "uilabel": "Output Commodity", 
             "uitype": "outcommodity"
            }, 
            "output": {
             "capacity": "out_buf_size", 
             "index": 4, 
             "shape": [-1, -1], 
             "type": ["cyclus::toolkit::ResBuf", "cyclus::Material"]
            }, 
            "streams_": {
             "alias": [
              "in_streams", 
              [
               "stream", 
               ["info", "mixing_ratio", "buf_size"], 
               [["commodities", "item"], "commodity", "pref"]
              ]
             ], 
             "doc": "", 
             "index": 0, 
             "shape": [-1, -1, -1, -1, -1, -1, -1, -1], 
             "tooltip": ["streams_", ["", ["", "", ""], [["", ""], "", ""]]], 
             "type": [
              "std::vector", 
              [
               "std::pair", 
               ["std::pair", "double", "double"], 
               ["std::map", "std::string", "double"]
              ]
             ], 
             "uilabel": ["streams_", ["", ["", "", ""], [["", ""], "", ""]]], 
             "uitype": [
              "oneormore", 
              ["pair", ["pair", "double", "double"], ["oneormore", "incommodity", "double"]]
             ]
            }, 
            "throughput": {
             "alias": "throughput", 
             "default": 1.000000000000000e+299, 
             "doc": "Maximum number of kg of fuel material that can be mixed per time step.", 
             "index": 5, 
             "range": [0.0, 1.000000000000000e+299], 
             "shape": [-1], 
             "tooltip": "throughput", 
             "type": "double", 
             "uilabel": "Maximum Throughput", 
             "uitype": "range", 
             "units": "kg"
            }
           }
          }, 
          ":cycamore:Reactor": {
           "all_parents": [
            "cyclus::Agent", 
            "cyclus::Facility", 
            "cyclus::Ider", 
            "cyclus::StateWrangler", 
            "cyclus::TimeListener", 
            "cyclus::Trader", 
            "cyclus::toolkit::AgentManaged", 
            "cyclus::toolkit::CommodityProducer", 
            "cyclus::toolkit::Position"
           ], 
           "doc": "Reactor is a simple, general reactor based on static compositional transformations to model fuel burnup.  The user specifies a set of input fuels and corresponding burnt compositions that fuel is transformed to when it is discharged from the core.  No incremental transmutation takes place. Rather, at the end of an operational cycle, the batch being discharged from the core is instantaneously transmuted from its original fresh fuel composition into its spent fuel form.\n\nEach fuel is identified by a specific input commodity and has an associated input recipe (nuclide composition), output recipe, output commidity, and preference.  The preference identifies which input fuels are preferred when requesting.  Changes in these preferences can be specified as a function of time using the pref_change variables.  Changes in the input-output recipe compositions can also be specified as a function of time using the recipe_change variables.\n\nThe reactor treats fuel as individual assemblies that are never split, combined or otherwise treated in any non-discrete way.  Fuel is requested in full-or-nothing assembly sized quanta.  If real-world assembly modeling is unnecessary, parameters can be adjusted (e.g. n_assem_core, assem_size, n_assem_batch).  At the end of every cycle, a full batch is discharged from the core consisting of n_assem_batch assemblies of assem_size kg. The reactor also has a specifiable refueling time period following the end of each cycle at the end of which it will resume operation on the next cycle *if* it has enough fuel for a full core; otherwise it waits until it has enough fresh fuel assemblies.\n\nIn addition to its core, the reactor has an on-hand fresh fuel inventory and a spent fuel inventory whose capacities are specified by n_assem_fresh and n_assem_spent respectively.  Each time step the reactor will attempt to acquire enough fresh fuel to fill its fresh fuel inventory (and its core if the core isn't currently full).  If the fresh fuel inventory has zero capacity, fuel will be ordered just-in-time after the end of each operational cycle before the next begins.  If the spent fuel inventory becomes full, the reactor will halt operation at the end of the next cycle until there is more room.  Each time step, the reactor will try to trade away as much of its spent fuel inventory as possible.\n\nWhen the reactor reaches the end of its lifetime, it will discharge all material from its core and trade away all its spent fuel as quickly as possible.  Full decommissioning will be delayed until all spent fuel is gone.  If the reactor has a full core when it is decommissioned (i.e. is mid-cycle) when the reactor is decommissioned, half (rounded up to nearest int) of its assemblies are transmuted to their respective burnt compositions.", 
           "entity": "facility", 
           "name": "cycamore::Reactor", 
           "niche": "reactor", 
           "parents": [
            "cyclus::Facility", 
            "cyclus::toolkit::CommodityProducer", 
            "cyclus::toolkit::Position"
           ], 
           "vars": {
            "assem_size": {
             "alias": "assem_size", 
             "doc": "Mass (kg) of a single assembly.", 
             "index": 9, 
             "range": [1.0, 100000.0], 
             "shape": [-1], 
             "tooltip": "assem_size", 
             "type": "double", 
             "uilabel": "Assembly Mass", 
             "uitype": "range", 
             "units": "kg"
            }, 
            "core": {
             "capacity": "n_assem_core * assem_size", 
             "index": 25, 
             "shape": [-1, -1], 
             "type": ["cyclus::toolkit::ResBuf", "cyclus::Material"]
            }, 
            "cycle_step": {
             "alias": "cycle_step", 
             "default": 0, 
             "doc": "Number of time steps since the start of the last cycle. Only set this if you know what you are doing", 
             "index": 16, 
             "shape": [-1], 
             "tooltip": "cycle_step", 
             "type": "int", 
             "uilabel": "Time Since Start of Last Cycle", 
             "units": "time steps"
            }, 
            "cycle_time": {
             "alias": "cycle_time", 
             "default": 18, 
             "doc": "The duration of a full operational cycle (excluding refueling time) in time steps.", 
             "index": 14, 
             "shape": [-1], 
             "tooltip": "cycle_time", 
             "type": "int", 
             "uilabel": "Cycle Length", 
             "units": "time steps"
            }, 
            "fresh": {
             "capacity": "n_assem_fresh * assem_size", 
             "index": 24, 
             "shape": [-1, -1], 
             "type": ["cyclus::toolkit::ResBuf", "cyclus::Material"]
            }, 
            "fuel_incommods": {
             "alias": ["fuel_incommods", "val"], 
             "doc": "Ordered list of input commodities on which to requesting fuel.", 
             "index": 0, 
             "shape": [-1, -1], 
             "tooltip": ["fuel_incommods", ""], 
             "type": ["std::vector", "std::string"], 
             "uilabel": ["Fresh Fuel Commodity List", ""], 
             "uitype": ["oneormore", "incommodity"]
            }, 
            "fuel_inrecipes": {
             "alias": ["fuel_inrecipes", "val"], 
             "doc": "Fresh fuel recipes to request for each of the given fuel input commodities (same order).", 
             "index": 1, 
             "shape": [-1, -1], 
             "tooltip": ["fuel_inrecipes", ""], 
             "type": ["std::vector", "std::string"], 
             "uilabel": ["Fresh Fuel Recipe List", ""], 
             "uitype": ["oneormore", "inrecipe"]
            }, 
            "fuel_outcommods": {
             "alias": ["fuel_outcommods", "val"], 
             "doc": "Output commodities on which to offer spent fuel originally received as each particular input commodity (same order).", 
             "index": 3, 
             "shape": [-1, -1], 
             "tooltip": ["fuel_outcommods", ""], 
             "type": ["std::vector", "std::string"], 
             "uilabel": ["Spent Fuel Commodity List", ""], 
             "uitype": ["oneormore", "outcommodity"]
            }, 
            "fuel_outrecipes": {
             "alias": ["fuel_outrecipes", "val"], 
             "doc": "Spent fuel recipes corresponding to the given fuel input commodities (same order). Fuel received via a particular input commodity is transmuted to the recipe specified here after being burned during a cycle.", 
             "index": 4, 
             "shape": [-1, -1], 
             "tooltip": ["fuel_outrecipes", ""], 
             "type": ["std::vector", "std::string"], 
             "uilabel": ["Spent Fuel Recipe List", ""], 
             "uitype": ["oneormore", "outrecipe"]
            }, 
            "fuel_prefs": {
             "alias": ["fuel_prefs", "val"], 
             "default": [], 
             "doc": "The preference for each type of fresh fuel requested corresponding to each input commodity (same order).  If no preferences are specified, 1.0 is used for all fuel requests (default).", 
             "index": 2, 
             "shape": [-1, -1], 
             "tooltip": ["fuel_prefs", ""], 
             "type": ["std::vector", "double"], 
             "uilabel": ["Fresh Fuel Preference List", ""]
            }, 
            "latitude": {
             "alias": "latitude", 
             "default": 0.0, 
             "doc": "Latitude of the agent's geographical position. The value should be expressed in degrees as a double.", 
             "index": 28, 
             "shape": [-1], 
             "tooltip": "latitude", 
             "type": "double", 
             "uilabel": "Geographical latitude in degrees as a double"
            }, 
            "longitude": {
             "alias": "longitude", 
             "default": 0.0, 
             "doc": "Longitude of the agent's geographical position. The value should be expressed in degrees as a double.", 
             "index": 29, 
             "shape": [-1], 
             "tooltip": "longitude", 
             "type": "double", 
             "uilabel": "Geographical longitude in degrees as a double"
            }, 
            "n_assem_batch": {
             "alias": "n_assem_batch", 
             "doc": "Number of assemblies that constitute a single batch.  This is the number of assemblies discharged from the core fully burned each cycle.Batch size is equivalent to ``n_assem_batch / n_assem_core``.", 
             "index": 10, 
             "shape": [-1], 
             "tooltip": "n_assem_batch", 
             "type": "int", 
             "uilabel": "Number of Assemblies per Batch"
            }, 
            "n_assem_core": {
             "alias": "n_assem_core", 
             "default": 3, 
             "doc": "Number of assemblies that constitute a full core.", 
             "index": 11, 
             "range": [1, 3], 
             "shape": [-1], 
             "tooltip": "n_assem_core", 
             "type": "int", 
             "uilabel": "Number of Assemblies in Core", 
             "uitype": "range"
            }, 
            "n_assem_fresh": {
             "alias": "n_assem_fresh", 
             "default": 0, 
             "doc": "Number of fresh fuel assemblies to keep on-hand if possible.", 
             "index": 12, 
             "range": [0, 3], 
             "shape": [-1], 
             "tooltip": "n_assem_fresh", 
             "type": "int", 
             "uilabel": "Minimum Fresh Fuel Inventory", 
             "uitype": "range", 
             "units": "assemblies"
            }, 
            "n_assem_spent": {
             "alias": "n_assem_spent", 
             "default": 1000000000, 
             "doc": "Number of spent fuel assemblies that can be stored on-site before reactor operation stalls.", 
             "index": 13, 
             "range": [0, 1000000000], 
             "shape": [-1], 
             "tooltip": "n_assem_spent", 
             "type": "int", 
             "uilabel": "Maximum Spent Fuel Inventory", 
             "uitype": "range", 
             "units": "assemblies"
            }, 
            "power_cap": {
             "alias": "power_cap", 
             "default": 0, 
             "doc": "Amount of electrical power the facility produces when operating normally.", 
             "index": 17, 
             "range": [0.0, 2000.0], 
             "shape": [-1], 
             "tooltip": "power_cap", 
             "type": "double", 
             "uilabel": "Nominal Reactor Power", 
             "uitype": "range", 
             "units": "MWe"
            }, 
            "power_name": {
             "alias": "power_name", 
             "default": "power", 
             "doc": "The name of the 'power' commodity used in conjunction with a deployment curve.", 
             "index": 18, 
             "shape": [-1], 
             "tooltip": "power_name", 
             "type": "std::string", 
             "uilabel": "Power Commodity Name"
            }, 
            "pref_change_commods": {
             "alias": ["pref_change_commods", "val"], 
             "default": [], 
             "doc": "The input commodity for a particular fuel preference change.  Same order as and direct correspondence to the specified preference change times.", 
             "index": 22, 
             "shape": [-1, -1], 
             "tooltip": ["pref_change_commods", ""], 
             "type": ["std::vector", "std::string"], 
             "uilabel": ["Commodity for Changed Fresh Fuel Preference", ""], 
             "uitype": ["oneormore", "incommodity"]
            }, 
            "pref_change_times": {
             "alias": ["pref_change_times", "val"], 
             "default": [], 
             "doc": "A time step on which to change the request preference for a particular fresh fuel type.", 
             "index": 21, 
             "shape": [-1, -1], 
             "tooltip": ["pref_change_times", ""], 
             "type": ["std::vector", "int"], 
             "uilabel": ["Time to Change Fresh Fuel Preference", ""]
            }, 
            "pref_change_values": {
             "alias": ["pref_change_values", "val"], 
             "default": [], 
             "doc": "The new/changed request preference for a particular fresh fuel. Same order as and direct correspondence to the specified preference change times.", 
             "index": 23, 
             "shape": [-1, -1], 
             "tooltip": ["pref_change_values", ""], 
             "type": ["std::vector", "double"], 
             "uilabel": ["Changed Fresh Fuel Preference", ""]
            }, 
            "recipe_change_commods": {
             "alias": ["recipe_change_commods", "val"], 
             "default": [], 
             "doc": "The input commodity indicating fresh fuel for which recipes will be changed. Same order as and direct correspondence to the specified recipe change times.", 
             "index": 6, 
             "shape": [-1, -1], 
             "tooltip": ["recipe_change_commods", ""], 
             "type": ["std::vector", "std::string"], 
             "uilabel": ["Commodity for Changed Fresh/Spent Fuel Recipe", ""], 
             "uitype": ["oneormore", "incommodity"]
            }, 
            "recipe_change_in": {
             "alias": ["recipe_change_in", "val"], 
             "default": [], 
             "doc": "The new input recipe to use for this recipe change. Same order as and direct correspondence to the specified recipe change times.", 
             "index": 7, 
             "shape": [-1, -1], 
             "tooltip": ["recipe_change_in", ""], 
             "type": ["std::vector", "std::string"], 
             "uilabel": ["New Recipe for Fresh Fuel", ""], 
             "uitype": ["oneormore", "inrecipe"]
            }, 
            "recipe_change_out": {
             "alias": ["recipe_change_out", "val"], 
             "default": [], 
             "doc": "The new output recipe to use for this recipe change. Same order as and direct correspondence to the specified recipe change times.", 
             "index": 8, 
             "shape": [-1, -1], 
             "tooltip": ["recipe_change_out", ""], 
             "type": ["std::vector", "std::string"], 
             "uilabel": ["New Recipe for Spent Fuel", ""], 
             "uitype": ["oneormore", "outrecipe"]
            }, 
            "recipe_change_times": {
             "alias": ["recipe_change_times", "val"], 
             "default": [], 
             "doc": "A time step on which to change the input-output recipe pair for a requested fresh fuel.", 
             "index": 5, 
             "shape": [-1, -1], 
             "tooltip": ["recipe_change_times", ""], 
             "type": ["std::vector", "int"], 
             "uilabel": ["Time to Change Fresh/Spent Fuel Recipe", ""]
            }, 
            "refuel_time": {
             "alias": "refuel_time", 
             "default": 1, 
             "doc": "The duration of a full refueling period - the minimum time between the end of a cycle and the start of the next cycle.", 
             "index": 15, 
             "shape": [-1], 
             "tooltip": "refuel_time", 
             "type": "int", 
             "uilabel": "Refueling Outage Duration", 
             "units": "time steps"
            }, 
            "res_indexes": {
             "alias": [["res_indexes", "item"], "key", "val"], 
             "default": {}, 
             "doc": "This should NEVER be set manually", 
             "index": 27, 
             "internal": true, 
             "shape": [-1, -1, -1], 
             "tooltip": [["res_indexes", ""], "", ""], 
             "type": ["std::map", "int", "int"], 
             "uilabel": [["res_indexes", ""], "", ""]
            }, 
            "side_product_quantity": {
             "alias": ["side_product_quantity", "val"], 
             "default": [], 
             "doc": "Ordered vector of the quantity of side product the reactor produces with power", 
             "index": 20, 
             "shape": [-1, -1], 
             "tooltip": ["side_product_quantity", ""], 
             "type": ["std::vector", "double"], 
             "uilabel": ["Quantity of Side Product from Reactor Plant", ""]
            }, 
            "side_products": {
             "alias": ["side_products", "val"], 
             "default": [], 
             "doc": "Ordered vector of side product the reactor produces with power", 
             "index": 19, 
             "shape": [-1, -1], 
             "tooltip": ["side_products", ""], 
             "type": ["std::vector", "std::string"], 
             "uilabel": ["Side Product from Reactor Plant", ""]
            }, 
            "spent": {
             "capacity": "n_assem_spent * assem_size", 
             "index": 26, 
             "shape": [-1, -1], 
             "type": ["cyclus::toolkit::ResBuf", "cyclus::Material"]
            }
           }
          }, 
          ":cycamore:Separations": {
           "all_parents": [
            "cyclus::Agent", 
            "cyclus::Facility", 
            "cyclus::Ider", 
            "cyclus::StateWrangler", 
            "cyclus::TimeListener", 
            "cyclus::Trader", 
            "cyclus::toolkit::Position"
           ], 
           "doc": "Separations processes feed material into one or more streams containing specific elements and/or nuclides.  It uses mass-based efficiencies.\n\nUser defined separations streams are specified as groups of component-efficiency pairs where 'component' means either a particular element or a particular nuclide.  Each component's paired efficiency represents the mass fraction of that component in the feed that is separated into that stream.  The efficiencies of a particular component across all streams must sum up to less than or equal to one.  If less than one, the remainining material is sent to a waste inventory and (potentially) traded away from there.\n\nThe facility receives material into a feed inventory that it processes with a specified throughput each time step.  Each output stream has a corresponding output inventory size/limit.  If the facility is unable to reduce its stocks by trading and hits this limit for any of its output streams, further processing/separations of feed material will halt until room is again available in the output streams.", 
           "entity": "facility", 
           "name": "cycamore::Separations", 
           "niche": "separations", 
           "parents": ["cyclus::Facility", "cyclus::toolkit::Position"], 
           "vars": {
            "feed": {
             "capacity": "feedbuf_size", 
             "index": 4, 
             "shape": [-1, -1], 
             "type": ["cyclus::toolkit::ResBuf", "cyclus::Material"]
            }, 
            "feed_commod_prefs": {
             "alias": ["feed_commod_prefs", "val"], 
             "default": [], 
             "doc": "Feed commodity request preferences for each of the given feed commodities (same order). If unspecified, default is to use 1.0 for all preferences.", 
             "index": 1, 
             "shape": [-1, -1], 
             "tooltip": ["feed_commod_prefs", ""], 
             "type": ["std::vector", "double"], 
             "uilabel": ["Feed Commodity Preference List", ""]
            }, 
            "feed_commods": {
             "alias": ["feed_commods", "val"], 
             "doc": "Ordered list of commodities on which to request feed material to separate. Order only matters for matching up with feed commodity preferences if specified.", 
             "index": 0, 
             "shape": [-1, -1], 
             "tooltip": ["feed_commods", ""], 
             "type": ["std::vector", "std::string"], 
             "uilabel": ["Feed Commodity List", ""], 
             "uitype": ["oneormore", "incommodity"]
            }, 
            "feed_recipe": {
             "alias": "feed_recipe", 
             "default": "", 
             "doc": "Name for recipe to be used in feed requests. Empty string results in use of a dummy recipe.", 
             "index": 2, 
             "shape": [-1], 
             "tooltip": "feed_recipe", 
             "type": "std::string", 
             "uilabel": "Feed Commodity Recipe List", 
             "uitype": "inrecipe"
            }, 
            "feedbuf_size": {
             "alias": "feedbuf_size", 
             "doc": "Maximum amount of feed material to keep on hand.", 
             "index": 3, 
             "shape": [-1], 
             "tooltip": "feedbuf_size", 
             "type": "double", 
             "uilabel": "Maximum Feed Inventory", 
             "units": "kg"
            }, 
            "latitude": {
             "alias": "latitude", 
             "default": 0.0, 
             "doc": "Latitude of the agent's geographical position. The value should be expressed in degrees as a double.", 
             "index": 11, 
             "shape": [-1], 
             "tooltip": "latitude", 
             "type": "double", 
             "uilabel": "Geographical latitude in degrees as a double"
            }, 
            "leftover": {
             "capacity": "leftoverbuf_size", 
             "index": 8, 
             "shape": [-1, -1], 
             "type": ["cyclus::toolkit::ResBuf", "cyclus::Material"]
            }, 
            "leftover_commod": {
             "alias": "leftover_commod", 
             "default": "default-waste-stream", 
             "doc": "Commodity on which to trade the leftover separated material stream. This MUST NOT be the same as any commodity used to define the other separations streams.", 
             "index": 6, 
             "shape": [-1], 
             "tooltip": "leftover_commod", 
             "type": "std::string", 
             "uilabel": "Leftover Commodity", 
             "uitype": "outcommodity"
            }, 
            "leftoverbuf_size": {
             "alias": "leftoverbuf_size", 
             "default": 1.000000000000000e+299, 
             "doc": "Maximum amount of leftover separated material (not included in any other stream) that can be stored. If full, the facility halts operation until space becomes available.", 
             "index": 7, 
             "range": [0.0, 1.000000000000000e+299], 
             "shape": [-1], 
             "tooltip": "leftoverbuf_size", 
             "type": "double", 
             "uilabel": "Maximum Leftover Inventory", 
             "uitype": "range", 
             "units": "kg"
            }, 
            "longitude": {
             "alias": "longitude", 
             "default": 0.0, 
             "doc": "Longitude of the agent's geographical position. The value should be expressed in degrees as a double.", 
             "index": 12, 
             "shape": [-1], 
             "tooltip": "longitude", 
             "type": "double", 
             "uilabel": "Geographical longitude in degrees as a double"
            }, 
            "streams": "streams_", 
            "streams_": {
             "alias": [
              ["streams", "item"], 
              "commod", 
              ["info", "buf_size", [["efficiencies", "item"], "comp", "eff"]]
             ], 
             "doc": "Output streams for separations. Each stream must have a unique name identifying the commodity on  which its material is traded, a max buffer capacity in kg (neg values indicate infinite size), and a set of component efficiencies. 'comp' is a component to be separated into the stream (e.g. U, Pu, etc.) and 'eff' is the mass fraction of the component that is separated from the feed into this output stream. If any stream buffer is full, the facility halts operation until space becomes available. The sum total of all component efficiencies across streams must be less than or equal to 1 (e.g. sum of U efficiencies for all streams must be <= 1).", 
             "index": 9, 
             "shape": [-1, -1, -1, -1, -1, -1, -1], 
             "tooltip": [["streams_", ""], "", ["", "", [["", ""], "", ""]]], 
             "type": [
              "std::map", 
              "std::string", 
              ["std::pair", "double", ["std::map", "int", "double"]]
             ], 
             "uilabel": [["Separations Streams and Efficiencies", ""], "", ["", "", [["", ""], "", ""]]], 
             "uitype": [
              "oneormore", 
              "outcommodity", 
              ["pair", "double", ["oneormore", "nuclide", "double"]]
             ]
            }, 
            "throughput": {
             "alias": "throughput", 
             "default": 1.000000000000000e+299, 
             "doc": "Maximum quantity of feed material that can be processed per time step.", 
             "index": 5, 
             "range": [0.0, 1.000000000000000e+299], 
             "shape": [-1], 
             "tooltip": "throughput", 
             "type": "double", 
             "uilabel": "Maximum Separations Throughput", 
             "uitype": "range", 
             "units": "kg/(time step)"
            }
           }
          }, 
          ":cycamore:Sink": {
           "all_parents": [
            "cyclus::Agent", 
            "cyclus::Facility", 
            "cyclus::Ider", 
            "cyclus::StateWrangler", 
            "cyclus::TimeListener", 
            "cyclus::Trader", 
            "cyclus::toolkit::Position"
           ], 
           "doc": " A sink facility that accepts materials and products with a fixed\n throughput (per time step) capacity and a lifetime capacity defined by\n a total inventory size. The inventory size and throughput capacity\n both default to infinite. If a recipe is provided, it will request\n material with that recipe. Requests are made for any number of\n specified commodities.\n", 
           "entity": "facility", 
           "name": "cycamore::Sink", 
           "parents": ["cyclus::Facility", "cyclus::toolkit::Position"], 
           "vars": {
            "capacity": {
             "alias": "capacity", 
             "default": 1.000000000000000e+299, 
             "doc": "capacity the sink facility can accept at each time step", 
             "index": 4, 
             "range": [0.0, 1.000000000000000e+299], 
             "shape": [-1], 
             "tooltip": "sink capacity", 
             "type": "double", 
             "uilabel": "Maximum Throughput", 
             "uitype": "range"
            }, 
            "in_commod_prefs": {
             "alias": ["in_commod_prefs", "val"], 
             "default": [], 
             "doc": "preferences for each of the given commodities, in the same order.Defauts to 1 if unspecified", 
             "index": 1, 
             "range": [null, [1.000000000000000e-299, 1.000000000000000e+299]], 
             "shape": [-1, -1], 
             "tooltip": ["in_commod_prefs", ""], 
             "type": ["std::vector", "double"], 
             "uilabel": ["In Commody Preferences", ""], 
             "uitype": ["oneormore", "range"]
            }, 
            "in_commods": {
             "alias": ["in_commods", "val"], 
             "doc": "commodities that the sink facility accepts", 
             "index": 0, 
             "shape": [-1, -1], 
             "tooltip": ["input commodities", ""], 
             "type": ["std::vector", "std::string"], 
             "uilabel": ["List of Input Commodities", ""], 
             "uitype": ["oneormore", "incommodity"]
            }, 
            "inventory": {
             "capacity": "max_inv_size", 
             "index": 5, 
             "shape": [-1, -1], 
             "type": ["cyclus::toolkit::ResBuf", "cyclus::Resource"]
            }, 
            "latitude": {
             "alias": "latitude", 
             "default": 0.0, 
             "doc": "Latitude of the agent's geographical position. The value should be expressed in degrees as a double.", 
             "index": 6, 
             "shape": [-1], 
             "tooltip": "latitude", 
             "type": "double", 
             "uilabel": "Geographical latitude in degrees as a double"
            }, 
            "longitude": {
             "alias": "longitude", 
             "default": 0.0, 
             "doc": "Longitude of the agent's geographical position. The value should be expressed in degrees as a double.", 
             "index": 7, 
             "shape": [-1], 
             "tooltip": "longitude", 
             "type": "double", 
             "uilabel": "Geographical longitude in degrees as a double"
            }, 
            "max_inv_size": {
             "alias": "max_inv_size", 
             "default": 1.000000000000000e+299, 
             "doc": "total maximum inventory size of sink facility", 
             "index": 3, 
             "range": [0.0, 1.000000000000000e+299], 
             "shape": [-1], 
             "tooltip": "sink maximum inventory size", 
             "type": "double", 
             "uilabel": "Maximum Inventory", 
             "uitype": "range"
            }, 
            "recipe_name": {
             "alias": "recipe_name", 
             "default": "", 
             "doc": "name of recipe to use for material requests, where the default (empty string) is to accept everything", 
             "index": 2, 
             "shape": [-1], 
             "tooltip": "requested composition", 
             "type": "std::string", 
             "uilabel": "Input Recipe", 
             "uitype": "inrecipe"
            }
           }
          }, 
          ":cycamore:Source": {
           "all_parents": [
            "cyclus::Agent", 
            "cyclus::Facility", 
            "cyclus::Ider", 
            "cyclus::StateWrangler", 
            "cyclus::TimeListener", 
            "cyclus::Trader", 
            "cyclus::toolkit::AgentManaged", 
            "cyclus::toolkit::CommodityProducer", 
            "cyclus::toolkit::Position"
           ], 
           "doc": "This facility acts as a source of material with a fixed throughput (per\ntime step) capacity and a lifetime capacity defined by a total inventory\nsize.  It offers its material as a single commodity. If a composition\nrecipe is specified, it provides that single material composition to\nrequesters.  If unspecified, the source provides materials with the exact\nrequested compositions.  The inventory size and throughput both default to\ninfinite.  Supplies material results in corresponding decrease in\ninventory, and when the inventory size reaches zero, the source can provide\nno more material.\n", 
           "entity": "facility", 
           "name": "cycamore::Source", 
           "parents": [
            "cyclus::Facility", 
            "cyclus::toolkit::CommodityProducer", 
            "cyclus::toolkit::Position"
           ], 
           "vars": {
            "inventory_size": {
             "alias": "inventory_size", 
             "default": 1.000000000000000e+299, 
             "doc": "Total amount of material this source has remaining. Every trade decreases this value by the supplied material quantity.  When it reaches zero, the source cannot provide any  more material.", 
             "index": 2, 
             "range": [0.0, 1.000000000000000e+299], 
             "shape": [-1], 
             "tooltip": "inventory_size", 
             "type": "double", 
             "uilabel": "Initial Inventory", 
             "uitype": "range", 
             "units": "kg"
            }, 
            "latitude": {
             "alias": "latitude", 
             "default": 0.0, 
             "doc": "Latitude of the agent's geographical position. The value should be expressed in degrees as a double.", 
             "index": 4, 
             "shape": [-1], 
             "tooltip": "latitude", 
             "type": "double", 
             "uilabel": "Geographical latitude in degrees as a double"
            }, 
            "longitude": {
             "alias": "longitude", 
             "default": 0.0, 
             "doc": "Longitude of the agent's geographical position. The value should be expressed in degrees as a double.", 
             "index": 5, 
             "shape": [-1], 
             "tooltip": "longitude", 
             "type": "double", 
             "uilabel": "Geographical longitude in degrees as a double"
            }, 
            "outcommod": {
             "alias": "outcommod", 
             "doc": "Output commodity on which the source offers material.", 
             "index": 0, 
             "shape": [-1], 
             "tooltip": "source output commodity", 
             "type": "std::string", 
             "uilabel": "Output Commodity", 
             "uitype": "outcommodity"
            }, 
            "outrecipe": {
             "alias": "outrecipe", 
             "default": "", 
             "doc": "Name of composition recipe that this source provides regardless of requested composition. If empty, source creates and provides whatever compositions are requested.", 
             "index": 1, 
             "shape": [-1], 
             "tooltip": "name of material recipe to provide", 
             "type": "std::string", 
             "uilabel": "Output Recipe", 
             "uitype": "outrecipe"
            }, 
            "throughput": {
             "alias": "throughput", 
             "default": 1.000000000000000e+299, 
             "doc": "amount of commodity that can be supplied at each time step", 
             "index": 3, 
             "range": [0.0, 1.000000000000000e+299], 
             "shape": [-1], 
             "tooltip": "per time step throughput", 
             "type": "double", 
             "uilabel": "Maximum Throughput", 
             "uitype": "range", 
             "units": "kg/(time step)"
            }
           }
          }, 
          ":cycamore:Storage": {
           "all_parents": [
            "cyclus::Agent", 
            "cyclus::Facility", 
            "cyclus::Ider", 
            "cyclus::StateWrangler", 
            "cyclus::TimeListener", 
            "cyclus::Trader", 
            "cyclus::toolkit::AgentManaged", 
            "cyclus::toolkit::CommodityProducer", 
            "cyclus::toolkit::Position"
           ], 
           "doc": "Storage is a simple facility which accepts any number of commodities and holds them for a user specified amount of time. The commodities accepted are chosen based on the specified preferences list. Once the desired amount of material has entered the facility it is passed into a 'processing' buffer where it is held until the residence time has passed. The material is then passed into a 'ready' buffer where it is queued for removal. Currently, all input commodities are lumped into a single output commodity. Storage also has the functionality to handle materials in discrete or continuous batches. Discrete mode, which is the default, does not split or combine material batches. Continuous mode, however, divides material batches if necessary in order to push materials through the facility as quickly as possible.", 
           "entity": "facility", 
           "name": "storage::Storage", 
           "parents": [
            "cyclus::Facility", 
            "cyclus::toolkit::CommodityProducer", 
            "cyclus::toolkit::Position"
           ], 
           "vars": {
            "in_commod_prefs": {
             "alias": ["in_commod_prefs", "val"], 
             "default": [], 
             "doc": "preferences for each of the given commodities, in the same order.Defauts to 1 if unspecified", 
             "index": 1, 
             "range": [null, [1.000000000000000e-299, 1.000000000000000e+299]], 
             "shape": [-1, -1], 
             "tooltip": ["in_commod_prefs", ""], 
             "type": ["std::vector", "double"], 
             "uilabel": ["In Commody Preferences", ""], 
             "uitype": ["oneormore", "range"]
            }, 
            "in_commods": {
             "alias": ["in_commods", "val"], 
             "doc": "commodities accepted by this facility", 
             "index": 0, 
             "shape": [-1, -1], 
             "tooltip": ["input commodity", ""], 
             "type": ["std::vector", "std::string"], 
             "uilabel": ["Input Commodities", ""], 
             "uitype": ["oneormore", "incommodity"]
            }, 
            "in_recipe": {
             "alias": "in_recipe", 
             "default": "", 
             "doc": "recipe accepted by this facility, if unspecified a dummy recipe is used", 
             "index": 3, 
             "shape": [-1], 
             "tooltip": "input recipe", 
             "type": "std::string", 
             "uilabel": "Input Recipe", 
             "uitype": "inrecipe"
            }, 
            "inventory": {
             "index": 7, 
             "shape": [-1, -1], 
             "tooltip": "Incoming material buffer", 
             "type": ["cyclus::toolkit::ResBuf", "cyclus::Material"]
            }, 
            "latitude": {
             "alias": "latitude", 
             "default": 0.0, 
             "doc": "Latitude of the agent's geographical position. The value should be expressed in degrees as a double.", 
             "index": 11, 
             "shape": [-1], 
             "tooltip": "latitude", 
             "type": "double", 
             "uilabel": "Geographical latitude in degrees as a double"
            }, 
            "longitude": {
             "alias": "longitude", 
             "default": 0.0, 
             "doc": "Longitude of the agent's geographical position. The value should be expressed in degrees as a double.", 
             "index": 12, 
             "shape": [-1], 
             "tooltip": "longitude", 
             "type": "double", 
             "uilabel": "Geographical longitude in degrees as a double"
            }, 
            "max_inv_size": {
             "alias": "max_inv_size", 
             "default": 1.000000000000000e+299, 
             "doc": "the maximum amount of material that can be in all storage buffer stages", 
             "index": 6, 
             "range": [0.0, 1.000000000000000e+299], 
             "shape": [-1], 
             "tooltip": "maximum inventory size (kg)", 
             "type": "double", 
             "uilabel": "Maximum Inventory Size", 
             "uitype": "range", 
             "units": "kg"
            }, 
            "out_commods": {
             "alias": ["out_commods", "val"], 
             "doc": "commodity produced by this facility. Multiple commodity tracking is currently not supported, one output commodity catches all input commodities.", 
             "index": 2, 
             "shape": [-1, -1], 
             "tooltip": ["output commodity", ""], 
             "type": ["std::vector", "std::string"], 
             "uilabel": ["Output Commodities", ""], 
             "uitype": ["oneormore", "outcommodity"]
            }, 
            "processing": {
             "index": 10, 
             "shape": [-1, -1], 
             "tooltip": "Buffer for material still waiting for required residence_time", 
             "type": ["cyclus::toolkit::ResBuf", "cyclus::Material"]
            }, 
            "ready": {
             "index": 9, 
             "shape": [-1, -1], 
             "tooltip": "Buffer for material held for required residence_time", 
             "type": ["cyclus::toolkit::ResBuf", "cyclus::Material"]
            }, 
            "residence_time": {
             "alias": "residence_time", 
             "default": 0, 
             "doc": "the minimum holding time for a received commodity (timesteps).", 
             "index": 4, 
             "range": [0, 12000], 
             "shape": [-1], 
             "tooltip": "residence time (timesteps)", 
             "type": "int", 
             "uilabel": "Residence Time", 
             "uitype": "range", 
             "units": "time steps"
            }, 
            "stocks": {
             "index": 8, 
             "shape": [-1, -1], 
             "tooltip": "Output material buffer", 
             "type": ["cyclus::toolkit::ResBuf", "cyclus::Material"]
            }, 
            "throughput": {
             "alias": "throughput", 
             "default": 1.000000000000000e+299, 
             "doc": "the max amount that can be moved through the facility per timestep (kg)", 
             "index": 5, 
             "range": [0.0, 1.000000000000000e+299], 
             "shape": [-1], 
             "tooltip": "throughput per timestep (kg)", 
             "type": "double", 
             "uilabel": "Throughput", 
             "uitype": "range", 
             "units": "kg"
            }
           }
          }
         }, 
         "schema": {
          ":agents:KFacility": "<interleave>\n    <element name=\"in_commod\">\n        <data type=\"token\"/>\n    </element>\n    <element name=\"recipe_name\">\n        <data type=\"token\"/>\n    </element>\n    <element name=\"out_commod\">\n        <data type=\"token\"/>\n    </element>\n    <element name=\"in_capacity\">\n        <data type=\"double\"/>\n    </element>\n    <element name=\"out_capacity\">\n        <data type=\"double\"/>\n    </element>\n    <optional>\n        <element name=\"current_capacity\">\n            <data type=\"double\"/>\n        </element>\n    </optional>\n    <optional>\n        <element name=\"max_inv_size\">\n            <data type=\"double\"/>\n        </element>\n    </optional>\n    <element name=\"k_factor_in\">\n        <data type=\"double\"/>\n    </element>\n    <element name=\"k_factor_out\">\n        <data type=\"double\"/>\n    </element>\n</interleave>\n", 
          ":agents:NullInst": "<text/>\n", 
          ":agents:NullRegion": "<text/>\n", 
          ":agents:Sink": "<interleave>\n    <element name=\"in_commods\">\n        <oneOrMore>\n            <element name=\"val\">\n                <data type=\"string\"/>\n            </element>\n        </oneOrMore>\n    </element>\n    <optional>\n        <element name=\"recipe_name\">\n            <data type=\"string\"/>\n        </element>\n    </optional>\n    <optional>\n        <element name=\"max_inv_size\">\n            <data type=\"double\"/>\n        </element>\n    </optional>\n    <element name=\"capacity\">\n        <data type=\"double\"/>\n    </element>\n</interleave>\n", 
          ":agents:Source": "<interleave>\n    <element name=\"commod\">\n        <data type=\"token\"/>\n    </element>\n    <optional>\n        <element name=\"recipe_name\">\n            <data type=\"token\"/>\n        </element>\n    </optional>\n    <element name=\"capacity\">\n        <data type=\"double\"/>\n    </element>\n</interleave>\n", 
          ":cycamore:DeployInst": "<interleave>\n    <element name=\"prototypes\">\n        <oneOrMore>\n            <element name=\"val\">\n                <data type=\"string\"/>\n            </element>\n        </oneOrMore>\n    </element>\n    <element name=\"build_times\">\n        <oneOrMore>\n            <element name=\"val\">\n                <data type=\"int\"/>\n            </element>\n        </oneOrMore>\n    </element>\n    <element name=\"n_build\">\n        <oneOrMore>\n            <element name=\"val\">\n                <data type=\"int\"/>\n            </element>\n        </oneOrMore>\n    </element>\n    <optional>\n        <element name=\"lifetimes\">\n            <oneOrMore>\n                <element name=\"val\">\n                    <data type=\"int\"/>\n                </element>\n            </oneOrMore>\n        </element>\n    </optional>\n    <optional>\n        <element name=\"latitude\">\n            <data type=\"double\"/>\n        </element>\n    </optional>\n    <optional>\n        <element name=\"longitude\">\n            <data type=\"double\"/>\n        </element>\n    </optional>\n</interleave>\n", 
          ":cycamore:Enrichment": "<interleave>\n    <element name=\"feed_commod\">\n        <data type=\"string\"/>\n    </element>\n    <element name=\"feed_recipe\">\n        <data type=\"string\"/>\n    </element>\n    <element name=\"product_commod\">\n        <data type=\"string\"/>\n    </element>\n    <element name=\"tails_commod\">\n        <data type=\"string\"/>\n    </element>\n    <optional>\n        <element name=\"tails_assay\">\n            <data type=\"double\"/>\n        </element>\n    </optional>\n    <optional>\n        <element name=\"initial_feed\">\n            <data type=\"double\"/>\n        </element>\n    </optional>\n    <optional>\n        <element name=\"max_feed_inventory\">\n            <data type=\"double\"/>\n        </element>\n    </optional>\n    <optional>\n        <element name=\"max_enrich\">\n            <data type=\"double\">\n                <param name=\"minInclusive\">0</param>\n                <param name=\"maxInclusive\">1</param>\n            </data>\n        </element>\n    </optional>\n    <optional>\n        <element name=\"swu_capacity\">\n            <data type=\"double\"/>\n        </element>\n    </optional>\n    <optional>\n        <element name=\"latitude\">\n            <data type=\"double\"/>\n        </element>\n    </optional>\n    <optional>\n        <element name=\"longitude\">\n            <data type=\"double\"/>\n        </element>\n    </optional>\n</interleave>\n", 
          ":cycamore:FuelFab": "<interleave>\n    <element name=\"fill_commods\">\n        <oneOrMore>\n            <element name=\"val\">\n                <data type=\"string\"/>\n            </element>\n        </oneOrMore>\n    </element>\n    <optional>\n        <element name=\"fill_commod_prefs\">\n            <oneOrMore>\n                <element name=\"val\">\n                    <data type=\"double\"/>\n                </element>\n            </oneOrMore>\n        </element>\n    </optional>\n    <element name=\"fill_recipe\">\n        <data type=\"string\"/>\n    </element>\n    <element name=\"fill_size\">\n        <data type=\"double\"/>\n    </element>\n    <element name=\"fiss_commods\">\n        <oneOrMore>\n            <element name=\"val\">\n                <data type=\"string\"/>\n            </element>\n        </oneOrMore>\n    </element>\n    <optional>\n        <element name=\"fiss_commod_prefs\">\n            <oneOrMore>\n                <element name=\"val\">\n                    <data type=\"double\"/>\n                </element>\n            </oneOrMore>\n        </element>\n    </optional>\n    <optional>\n        <element name=\"fiss_recipe\">\n            <data type=\"string\"/>\n        </element>\n    </optional>\n    <element name=\"fiss_size\">\n        <data type=\"double\"/>\n    </element>\n    <optional>\n        <element name=\"topup_commod\">\n            <data type=\"string\"/>\n        </element>\n    </optional>\n    <optional>\n        <element name=\"topup_pref\">\n            <data type=\"double\"/>\n        </element>\n    </optional>\n    <optional>\n        <element name=\"topup_recipe\">\n            <data type=\"string\"/>\n        </element>\n    </optional>\n    <optional>\n        <element name=\"topup_size\">\n            <data type=\"double\"/>\n        </element>\n    </optional>\n    <element name=\"outcommod\">\n        <data type=\"string\"/>\n    </element>\n    <optional>\n        <element name=\"throughput\">\n            <data type=\"double\"/>\n        </element>\n    </optional>\n    <element name=\"spectrum\">\n        <data type=\"string\"/>\n    </element>\n    <optional>\n        <element name=\"latitude\">\n            <data type=\"double\"/>\n        </element>\n    </optional>\n    <optional>\n        <element name=\"longitude\">\n            <data type=\"double\"/>\n        </element>\n    </optional>\n</interleave>\n", 
          ":cycamore:GrowthRegion": "<interleave>\n    <element name=\"growth\">\n        <oneOrMore>\n            <element name=\"item\">\n                <interleave>\n                    <element name=\"commod\">\n                        <data type=\"string\"/>\n                    </element>\n                    <element name=\"piecewise_function\">\n                        <oneOrMore>\n                            <element name=\"piece\">\n                                <interleave>\n                                    <element name=\"start\">\n                                        <data type=\"int\"/>\n                                    </element>\n                                    <element name=\"function\">\n                                        <interleave>\n                                            <element name=\"type\">\n                                                <data type=\"string\"/>\n                                            </element>\n                                            <element name=\"params\">\n                                                <data type=\"string\"/>\n                                            </element>\n                                        </interleave>\n                                    </element>\n                                </interleave>\n                            </element>\n                        </oneOrMore>\n                    </element>\n                </interleave>\n            </element>\n        </oneOrMore>\n    </element>\n    <optional>\n        <element name=\"latitude\">\n            <data type=\"double\"/>\n        </element>\n    </optional>\n    <optional>\n        <element name=\"longitude\">\n            <data type=\"double\"/>\n        </element>\n    </optional>\n</interleave>\n", 
          ":cycamore:ManagerInst": "<interleave>\n    <element name=\"prototypes\">\n        <oneOrMore>\n            <element name=\"val\">\n                <data type=\"string\"/>\n            </element>\n        </oneOrMore>\n    </element>\n    <optional>\n        <element name=\"latitude\">\n            <data type=\"double\"/>\n        </element>\n    </optional>\n    <optional>\n        <element name=\"longitude\">\n            <data type=\"double\"/>\n        </element>\n    </optional>\n</interleave>\n", 
          ":cycamore:Mixer": "<interleave>\n    <element name=\"in_streams\">\n        <oneOrMore>\n            <element name=\"stream\">\n                <interleave>\n                    <element name=\"info\">\n                        <interleave>\n                            <element name=\"mixing_ratio\">\n                                <data type=\"double\"/>\n                            </element>\n                            <element name=\"buf_size\">\n                                <data type=\"double\"/>\n                            </element>\n                        </interleave>\n                    </element>\n                    <element name=\"commodities\">\n                        <oneOrMore>\n                            <element name=\"item\">\n                                <interleave>\n                                    <element name=\"commodity\">\n                                        <data type=\"string\"/>\n                                    </element>\n                                    <element name=\"pref\">\n                                        <data type=\"double\"/>\n                                    </element>\n                                </interleave>\n                            </element>\n                        </oneOrMore>\n                    </element>\n                </interleave>\n            </element>\n        </oneOrMore>\n    </element>\n    <element name=\"out_commod\">\n        <data type=\"string\"/>\n    </element>\n    <optional>\n        <element name=\"out_buf_size\">\n            <data type=\"double\"/>\n        </element>\n    </optional>\n    <optional>\n        <element name=\"throughput\">\n            <data type=\"double\"/>\n        </element>\n    </optional>\n    <optional>\n        <element name=\"latitude\">\n            <data type=\"double\"/>\n        </element>\n    </optional>\n    <optional>\n        <element name=\"longitude\">\n            <data type=\"double\"/>\n        </element>\n    </optional>\n</interleave>\n", 
          ":cycamore:Reactor": "<interleave>\n    <element name=\"fuel_incommods\">\n        <oneOrMore>\n            <element name=\"val\">\n                <data type=\"string\"/>\n            </element>\n        </oneOrMore>\n    </element>\n    <element name=\"fuel_inrecipes\">\n        <oneOrMore>\n            <element name=\"val\">\n                <data type=\"string\"/>\n            </element>\n        </oneOrMore>\n    </element>\n    <optional>\n        <element name=\"fuel_prefs\">\n            <oneOrMore>\n                <element name=\"val\">\n                    <data type=\"double\"/>\n                </element>\n            </oneOrMore>\n        </element>\n    </optional>\n    <element name=\"fuel_outcommods\">\n        <oneOrMore>\n            <element name=\"val\">\n                <data type=\"string\"/>\n            </element>\n        </oneOrMore>\n    </element>\n    <element name=\"fuel_outrecipes\">\n        <oneOrMore>\n            <element name=\"val\">\n                <data type=\"string\"/>\n            </element>\n        </oneOrMore>\n    </element>\n    <optional>\n        <element name=\"recipe_change_times\">\n            <oneOrMore>\n                <element name=\"val\">\n                    <data type=\"int\"/>\n                </element>\n            </oneOrMore>\n        </element>\n    </optional>\n    <optional>\n        <element name=\"recipe_change_commods\">\n            <oneOrMore>\n                <element name=\"val\">\n                    <data type=\"string\"/>\n                </element>\n            </oneOrMore>\n        </element>\n    </optional>\n    <optional>\n        <element name=\"recipe_change_in\">\n            <oneOrMore>\n                <element name=\"val\">\n                    <data type=\"string\"/>\n                </element>\n            </oneOrMore>\n        </element>\n    </optional>\n    <optional>\n        <element name=\"recipe_change_out\">\n            <oneOrMore>\n                <element name=\"val\">\n                    <data type=\"string\"/>\n                </element>\n            </oneOrMore>\n        </element>\n    </optional>\n    <element name=\"assem_size\">\n        <data type=\"double\"/>\n    </element>\n    <element name=\"n_assem_batch\">\n        <data type=\"int\"/>\n    </element>\n    <optional>\n        <element name=\"n_assem_core\">\n            <data type=\"int\"/>\n        </element>\n    </optional>\n    <optional>\n        <element name=\"n_assem_fresh\">\n            <data type=\"int\"/>\n        </element>\n    </optional>\n    <optional>\n        <element name=\"n_assem_spent\">\n            <data type=\"int\"/>\n        </element>\n    </optional>\n    <optional>\n        <element name=\"cycle_time\">\n            <data type=\"int\"/>\n        </element>\n    </optional>\n    <optional>\n        <element name=\"refuel_time\">\n            <data type=\"int\"/>\n        </element>\n    </optional>\n    <optional>\n        <element name=\"cycle_step\">\n            <data type=\"int\"/>\n        </element>\n    </optional>\n    <optional>\n        <element name=\"power_cap\">\n            <data type=\"double\"/>\n        </element>\n    </optional>\n    <optional>\n        <element name=\"power_name\">\n            <data type=\"string\"/>\n        </element>\n    </optional>\n    <optional>\n        <element name=\"side_products\">\n            <oneOrMore>\n                <element name=\"val\">\n                    <data type=\"string\"/>\n                </element>\n            </oneOrMore>\n        </element>\n    </optional>\n    <optional>\n        <element name=\"side_product_quantity\">\n            <oneOrMore>\n                <element name=\"val\">\n                    <data type=\"double\"/>\n                </element>\n            </oneOrMore>\n        </element>\n    </optional>\n    <optional>\n        <element name=\"pref_change_times\">\n            <oneOrMore>\n                <element name=\"val\">\n                    <data type=\"int\"/>\n                </element>\n            </oneOrMore>\n        </element>\n    </optional>\n    <optional>\n        <element name=\"pref_change_commods\">\n            <oneOrMore>\n                <element name=\"val\">\n                    <data type=\"string\"/>\n                </element>\n            </oneOrMore>\n        </element>\n    </optional>\n    <optional>\n        <element name=\"pref_change_values\">\n            <oneOrMore>\n                <element name=\"val\">\n                    <data type=\"double\"/>\n                </element>\n            </oneOrMore>\n        </element>\n    </optional>\n    <optional>\n        <element name=\"latitude\">\n            <data type=\"double\"/>\n        </element>\n    </optional>\n    <optional>\n        <element name=\"longitude\">\n            <data type=\"double\"/>\n        </element>\n    </optional>\n</interleave>\n", 
          ":cycamore:Separations": "<interleave>\n    <element name=\"feed_commods\">\n        <oneOrMore>\n            <element name=\"val\">\n                <data type=\"string\"/>\n            </element>\n        </oneOrMore>\n    </element>\n    <optional>\n        <element name=\"feed_commod_prefs\">\n            <oneOrMore>\n                <element name=\"val\">\n                    <data type=\"double\"/>\n                </element>\n            </oneOrMore>\n        </element>\n    </optional>\n    <optional>\n        <element name=\"feed_recipe\">\n            <data type=\"string\"/>\n        </element>\n    </optional>\n    <element name=\"feedbuf_size\">\n        <data type=\"double\"/>\n    </element>\n    <optional>\n        <element name=\"throughput\">\n            <data type=\"double\"/>\n        </element>\n    </optional>\n    <optional>\n        <element name=\"leftover_commod\">\n            <data type=\"string\"/>\n        </element>\n    </optional>\n    <optional>\n        <element name=\"leftoverbuf_size\">\n            <data type=\"double\"/>\n        </element>\n    </optional>\n    <element name=\"streams\">\n        <oneOrMore>\n            <element name=\"item\">\n                <interleave>\n                    <element name=\"commod\">\n                        <data type=\"string\"/>\n                    </element>\n                    <element name=\"info\">\n                        <interleave>\n                            <element name=\"buf_size\">\n                                <data type=\"double\"/>\n                            </element>\n                            <element name=\"efficiencies\">\n                                <oneOrMore>\n                                    <element name=\"item\">\n                                        <interleave>\n                                            <element name=\"comp\">\n                                                <data type=\"string\"/>\n                                            </element>\n                                            <element name=\"eff\">\n                                                <data type=\"double\"/>\n                                            </element>\n                                        </interleave>\n                                    </element>\n                                </oneOrMore>\n                            </element>\n                        </interleave>\n                    </element>\n                </interleave>\n            </element>\n        </oneOrMore>\n    </element>\n    <optional>\n        <element name=\"latitude\">\n            <data type=\"double\"/>\n        </element>\n    </optional>\n    <optional>\n        <element name=\"longitude\">\n            <data type=\"double\"/>\n        </element>\n    </optional>\n</interleave>\n", 
          ":cycamore:Sink": "<interleave>\n    <element name=\"in_commods\">\n        <oneOrMore>\n            <element name=\"val\">\n                <data type=\"string\"/>\n            </element>\n        </oneOrMore>\n    </element>\n    <optional>\n        <element name=\"in_commod_prefs\">\n            <oneOrMore>\n                <element name=\"val\">\n                    <data type=\"double\"/>\n                </element>\n            </oneOrMore>\n        </element>\n    </optional>\n    <optional>\n        <element name=\"recipe_name\">\n            <data type=\"string\"/>\n        </element>\n    </optional>\n    <optional>\n        <element name=\"max_inv_size\">\n            <data type=\"double\"/>\n        </element>\n    </optional>\n    <optional>\n        <element name=\"capacity\">\n            <data type=\"double\"/>\n        </element>\n    </optional>\n    <optional>\n        <element name=\"latitude\">\n            <data type=\"double\"/>\n        </element>\n    </optional>\n    <optional>\n        <element name=\"longitude\">\n            <data type=\"double\"/>\n        </element>\n    </optional>\n</interleave>\n", 
          ":cycamore:Source": "<interleave>\n    <element name=\"outcommod\">\n        <data type=\"string\"/>\n    </element>\n    <optional>\n        <element name=\"outrecipe\">\n            <data type=\"string\"/>\n        </element>\n    </optional>\n    <optional>\n        <element name=\"inventory_size\">\n            <data type=\"double\"/>\n        </element>\n    </optional>\n    <optional>\n        <element name=\"throughput\">\n            <data type=\"double\"/>\n        </element>\n    </optional>\n    <optional>\n        <element name=\"latitude\">\n            <data type=\"double\"/>\n        </element>\n    </optional>\n    <optional>\n        <element name=\"longitude\">\n            <data type=\"double\"/>\n        </element>\n    </optional>\n</interleave>\n", 
          ":cycamore:Storage": "<interleave>\n    <element name=\"in_commods\">\n        <oneOrMore>\n            <element name=\"val\">\n                <data type=\"string\"/>\n            </element>\n        </oneOrMore>\n    </element>\n    <optional>\n        <element name=\"in_commod_prefs\">\n            <oneOrMore>\n                <element name=\"val\">\n                    <data type=\"double\"/>\n                </element>\n            </oneOrMore>\n        </element>\n    </optional>\n    <element name=\"out_commods\">\n        <oneOrMore>\n            <element name=\"val\">\n                <data type=\"string\"/>\n            </element>\n        </oneOrMore>\n    </element>\n    <optional>\n        <element name=\"in_recipe\">\n            <data type=\"string\"/>\n        </element>\n    </optional>\n    <optional>\n        <element name=\"residence_time\">\n            <data type=\"int\"/>\n        </element>\n    </optional>\n    <optional>\n        <element name=\"throughput\">\n            <data type=\"double\"/>\n        </element>\n    </optional>\n    <optional>\n        <element name=\"max_inv_size\">\n            <data type=\"double\"/>\n        </element>\n    </optional>\n    <optional>\n        <element name=\"latitude\">\n            <data type=\"double\"/>\n        </element>\n    </optional>\n    <optional>\n        <element name=\"longitude\">\n            <data type=\"double\"/>\n        </element>\n    </optional>\n</interleave>\n"
         }, 
         "specs": [
          ":agents:KFacility", 
          ":agents:NullInst", 
          ":agents:NullRegion", 
          ":agents:Sink", 
          ":agents:Source", 
          ":cycamore:DeployInst", 
          ":cycamore:Enrichment", 
          ":cycamore:FuelFab", 
          ":cycamore:GrowthRegion", 
          ":cycamore:ManagerInst", 
          ":cycamore:Mixer", 
          ":cycamore:Reactor", 
          ":cycamore:Separations", 
          ":cycamore:Sink", 
          ":cycamore:Source", 
          ":cycamore:Storage"
         ]
        }"""


