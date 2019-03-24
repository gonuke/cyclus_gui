from tkinter import *
from PIL import Image, ImageTk
from tkinter import messagebox
from tkinter import filedialog
from tkinter.scrolledtext import ScrolledText
import xml.etree.ElementTree as et
import xmltodict
import uuid
import os
import shutil
import json
import copy


class PrototypeWindow(Frame):
    def __init__(self, master, output_path):
        """
        proto_dict looks like:

        """
        self.master = Toplevel(master)
        self.master.title('Add prototypes')
        self.output_path = output_path
        self.master.geometry('+0+700')
        self.guide()
        Label(self.master, text='Choose an archetype to add:').grid(row=0)
        self.get_schema()
        self.proto_dict = {}
        if os.path.isfile(os.path.join(self.output_path, 'prototypes.xml')):
            self.read_xml()
        self.load_archetypes()

        self.tkvar = StringVar(self.master)
        archetypes = [x[0] + ':' + x[1] for x in self.arches]
        archetypes = [x for x in archetypes if 'inst' not in x.lower()]
        archetypes = [x for x in archetypes if 'region' not in x.lower()]
        self.tkvar.set('\t\t')
        OptionMenu(self.master, self.tkvar, *archetypes).grid(row=1)
        self.tkvar.trace('w', self.definition_window)

        Button(self.master, text='Done', command= lambda : self.submit()).grid(row=2)

        self.status_window = Toplevel(self.master)
        self.status_window.title('Defined prototypes')
        self.status_window.geometry('+250+700')
        Label(self.status_window, text='Defined Prototypes:').pack()
        self.status_var = StringVar()
        self.status_var.set('')
        self.update_loaded_modules()
        Label(self.status_window, textvariable=self.status_var).pack()


    def get_schema(self):
        # get from cyclus -m
        path = os.path.join(self.output_path, 'm.json')
        if os.path.isfile(path):
            with open(path, 'r') as f:
                jtxt = f.read()
            j = json.loads(jtxt)

        else:
            messagebox.showinfo('Cyclus not found', 'Cyclus is not found, Using documentation from packaged json.')
            with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'src/metadata.json'), 'r') as f:
                jtxt = f.read()
            j = json.loads(jtxt)

        # get documentation for variable and archetype
        self.doc_dict = {}
        self.type_dict = {}
        self.default_dict = {}
        for arche, cat_dict in j['annotations'].items():
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
        j['schema'] = {k:v for k,v in j['schema'].items() if 'region' not in k.lower()}
        j['schema'] = {k:v for k,v in j['schema'].items() if 'inst' not in k.lower()}
        for arche, xml in j['schema'].items():
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


    def load_archetypes(self):
        # get from archetypes definition
        self.arches = []
        with open(os.path.join(self.output_path, 'archetypes.xml'), 'r') as f:
            xml_dict = xmltodict.parse(f.read())['archetypes']
        for entry in xml_dict['spec']:
            # ignore institutions and regions
            if 'region' not in entry['name'].lower() or 'inst' not in entry['name'].lower():
                self.arches.append([entry['lib'], entry['name']])


    def update_loaded_modules(self):
        string = ''
        for name, val in self.proto_dict.items():
            string += '%s (%s)\n' %(name, val['archetype'])
        self.status_var.set(string)


    def submit(self):
        new_dict = {'root': {'facility': []}}
        if len(self.proto_dict) == 0:
            messagebox.showerror('Nope', 'You have not defined any prototypes yet.')
            return
        with open(os.path.join(self.output_path, 'prototypes.xml'), 'w') as f:
            for name, config in self.proto_dict.items():
                facility_dict = {}
                facility_dict['name'] = name
                facility_dict['config'] = config['config']
                new_dict['root']['facility'].append(facility_dict)
            f.write(xmltodict.unparse(new_dict, pretty=True))
        messagebox.showinfo('Sucess', 'Successfully rendered %i prototypes!' %len(new_dict['root']['facility']))
        self.master.destroy()



    def definition_window(self, *args):
        self.def_window = Toplevel(self.master)
        self.def_window.title('Define prototype')
        self.def_window.geometry('+700+1000')
        archetype = self.tkvar.get()
        Label(self.def_window, text='%s' %archetype).grid(row=0, columnspan=2)

        proto_name_entry = Entry(self.def_window)
        proto_name_entry.grid(row=1, column=1)
        Button(self.def_window, text='Done', command=lambda : self.submit_proto(archetype, proto_name_entry.get())).grid(row=0, column=2)
        Label(self.def_window, text='Prototype Name:').grid(row=1, column=0)
        
        self.def_entries(archetype)

    def submit_proto(self, archetype, proto_name):
        if proto_name == '':
            messagebox.showerror('Error', 'You must define the prototype name')
            return
        archetype_name = archetype.split(':')[-1]
        config_dict = {archetype_name: {}}
        # .get() all the entries
        for param, row_val_dict in self.entry_dict.items():
            for rownum, val_list in row_val_dict.items():
                if isinstance(val_list, list):
                    val_list = [x.get() for x in val_list]
                    val_list = [x for x in val_list if x != '']
                    if len(val_list) == 0:
                        continue
                    # change tag with param by referencing
                    # tag_dict
                    try:
                        tag = self.tag_dict[archetype][param]
                    except:
                        tag = self.tag_dict[archetype][param + '*']
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
        
        self.proto_dict[proto_name] = {'archetype': archetype_name,
                                       'config': config_dict}
        messagebox.showinfo('Success', 'Successfully created %s prototype %s' %(archetype_name, proto_name))
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
        if archetype in self.param_dict.keys():
            oneormore = self.param_dict[archetype]['oneormore']
            if 'streams' in oneormore:
                oneormore.remove('streams')
            if 'in_streams' in oneormore:
                oneormore.remove('in_streams')
            one = self.param_dict[archetype]['one']

        for val in oneormore:
            start_row += 1
            self.add_row_oneormore(val, self.def_window, start_row)

        for  val in one:
            start_row += 1
            self.add_row(val, self.def_window, start_row)   
            # add color for non-essential parameters


        start_row += 1
        if archetype == 'cycamore:Separations':
            # special treatment for separations
            # add stream
            Button(self.def_window, text='Add output Stream', command=lambda:self.add_sep_stream()).grid(row=start_row, columnspan=3)
            self.entry_dict['streams'] = {9999: {'item': []}}

        if archetype == 'cycamore:Mixer':
            Button(self.def_window, text='Add input Stream', command=lambda:self.add_mix_stream()).grid(row=start_row, columnspan=3)
            self.entry_dict['in_streams'] = {9999: {'stream': []}}


    def proto_guide_window(self, archetype):
        proto_guide_window_ = Toplevel(self.def_window)
        proto_guide_window_.title('%s documentation' %archetype)
        proto_guide_window_.geometry('+0+1000')
        string = archetype + '\n'
        # documentation for archetype
        input_variables = self.param_dict[archetype]['oneormore'] + self.param_dict[archetype]['one']
        input_variables = [x.replace('*', '') for x in input_variables]
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
        t = Text(proto_guide_window_)
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
        self.el_ef_entry_list = [[x[0].get(), x[1].get()] for x in self.el_ef_entry_list]
        for i in self.el_ef_entry_list:
            if i[0] == i[1] == '':
                continue
            elif i[0] == '' or i[1] == '':
                messagebox.showerror('Error', 'Stream element and efficiency missing')
                return 
            sep_stream_dict['info']['efficiencies']['item'].append({'comp': i[0], 'eff': i[1]})
        if len(sep_stream_dict['info']['efficiencies']['item']) != 0:
            messagebox.showerror('Error', 'You did not define a single stream')
            return  
        self.entry_dict['streams'][9999]['item'].append(sep_stream_dict)
        messagebox.showinfo('Success', 'Succesfully added separation stream')
        self.sep_stream_window.destroy()


    def add_sep_row(self):
        el = Entry(self.sep_stream_window)
        el.grid(row=self.sep_row_num, column=0)
        ef = Entry(self.sep_stream_window)
        ef.grid(row=self.sep_row_num, column=1)
        self.el_ef_entry_list.append([el, ef])
        self.sep_row_num += 1

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
        self.entry_dict['in_streams'][9999]['stream'].append(mix_stream_dict)
        messagebox.showinfo('Success', 'Succesfully added separation stream')
        self.mix_stream_window.destroy()


    def add_mix_row(self):
        commod = Entry(self.mix_stream_window)
        commod.grid(row=self.mix_row_num, column=0)
        pref = Entry(self.mix_stream_window)
        pref.grid(row=self.mix_row_num, column=1)
        self.commod_pref_entry_list.append([commod, pref])
        self.mix_row_num += 1
        


    def add_row(self, label, master, rownum, color='black'):
        if '*' in label:
            color = 'red'
        label = label.replace('*', '')
        Label(master, text=label, fg=color).grid(row=rownum, column=1)
        self.entry_dict[label] = {rownum: Entry(self.def_window)}
        self.entry_dict[label][rownum].grid(row=rownum, column=2)


    def add_row_oneormore(self, label, master, rownum, color='black'):
        if '*' in label:
            color = 'red'
        label = label.replace('*', '')
        Label(master, text=label, fg=color).grid(row=rownum, column=1)
        self.entry_dict[label] = {rownum : []}
        Button(master, text='Add', command=lambda : self.add_entry(label, rownum)).grid(row=rownum, column=0)


    def add_entry(self, label, rownum):
        col = len(self.entry_dict[label][rownum]) + 2
        self.entry_dict[label][rownum].append(Entry(self.def_window))
        self.entry_dict[label][rownum][-1].grid(row=rownum, column=col)


    def read_xml(self):
        with open(os.path.join(self.output_path, 'prototypes.xml'), 'r') as f:
            xml_list = xmltodict.parse(f.read())['root']['facility']
            for facility in xml_list:
                if isinstance(facility, str):
                    facility_name = xml_list['name']
                    archetype = list(xml_list['config'].keys())[0]
                    self.proto_dict[facility_name] = {'archetype': archetype,
                                                      'config': {archetype: xml_list['config'][archetype]}}
                    break

                facility_name = facility['name']
                archetype = list(facility['config'].keys())[0]
                self.proto_dict[facility_name] = {'archetype': archetype,
                                                  'config': facility['config'][archetype]}


    def guide(self):

        self.guide_window = Toplevel(self.master)
        self.guide_window.title('Prototypes guide')
        self.guide_window.geometry('+0+400')
        guide_text = """
        Here you define archetypes with specific parameters to use in the simulation.
        An archetype is the code (general behavior of facility - e.g. reactor facility )
        A prototype is an archetype + user-defined parameters 
        (e.g. reactor with 3 60-assembly batches and 1000MWe power output).

        Here you can add prototypes by taking an archetype template and defining
        your parameters.

        Click on the dropdown to select the archetype you want to add, 
        and two windows will pop up. One is the documentation for the
        archetype and the parameters, and the other is the one you should
        fill out. The red parameters have default values (specified in 
        documnetation window), thus are optional. The parameters with 'Add'
        button next to it are parameters with (potentially) more than one
        variables. You can add more values by clicking 'Add'. Fill out
        the prototype name and the parameters, then click 'Done' to
        save the prototye. The window with 'Defined Archetypes' will update
        as you define prototypes 

        """
        Label(self.guide_window, text=guide_text, justify=LEFT).pack(padx=30, pady=30)

