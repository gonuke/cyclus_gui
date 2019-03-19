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

uniq_id = str(uuid.uuid4())[:3]
file_path = os.path.abspath(os.path.dirname(__file__))

# generate unique id
folders = os.listdir(file_path)
folders = [f for f in folders if os.path.isdir(os.path.join(file_path, f))]
unique = False
while not unique:
    for folder in folders:
        if uniq_id in folder:
            print('JACKPOT! You have two identical 3 random letternumbers! Today is your lucky day go buy a lottery')
            uniq_id = str(uuid.uuid4())[:3]
            continue
    unique = True

output_path = os.path.join(file_path, 'output_'+uniq_id)
os.mkdir(output_path)
print('This your id boy:', uniq_id)


class Cygui(Frame):
    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.master = master
        self.init_window()
        self.guide()

    def init_window(self):
        self.master.title('GUI')
        self.pack(fill=BOTH, expand=1)

        # menu instance
        menu = Menu(self.master)
        self.master.config(menu=menu)

        self.hash_var = StringVar()
        self.hash_var.set(uniq_id)
        file = Menu(menu)
        file.add_command(label='Exit', command=self.client_exit)
        menu.add_cascade(label='File', menu=file)

        edit = Menu(menu)
        edit.add_command(label='undo')
        edit.add_command(label='copy')
        # this cascade will have all the commands in edit
        menu.add_cascade(label='Edit', menu=edit)


        Label(root, text='Cyclus Input generator').pack()
        Label(root, textvariable=self.hash_var).pack()

        sim_button = Button(root, text='Simulation', command=lambda : self.open_window('simulation'))
        sim_button.pack()

        library_button = Button(root, text='Libraries', command=lambda : self.open_window('archetype'))
        library_button.pack()

        prototype_button = Button(root, text='Prototypes', command=lambda : self.open_window('prototype'))
        prototype_button.pack()

        region_button = Button(root, text='Regions', command=lambda : self.open_window('region'))
        region_button.pack()

        recipe_button = Button(root, text='Recipes', command=lambda : self.open_window('recipe'))
        recipe_button.pack()

        load_button = Button(root, text='Load', command=lambda: self.load_prev_window())
        load_button.pack()

        make_input_button = Button(root, text='Generate Input', command=lambda: self.check_and_run(run=False))
        make_input_button.pack()

        done_button = Button(root, text='Combine and Run', command= lambda: self.check_and_run())
        done_button.pack()



    def client_exit(self):
        exit()

    def showImg(self, image_path):
        load = Image.open(image_path)
        render = ImageTk.PhotoImage(load)

        img = Label(self, image=render)
        img.image = render
        img.place(x=0, y=0)

    def showTxt(self, text):
        text = Label(self, text=text)
        text.pack()

    def open_window(self, name):
        if name == 'simulation':
            self.app = SimulationWindow(self.master)
        if name == 'archetype':
            self.app = ArchetypeWindow(self.master)
        if name == 'prototype':
            if not os.path.isfile(os.path.join(output_path, 'archetypes.xml')):
                messagebox.showerror('Error', 'You must define the Archetype libraries first!')
                return
            self.app = PrototypeWindow(self.master)
        if name == 'region':
            self.app = RegionWindow(self.master)
        if name == 'recipe':
            self.app = RecipeWindow(self.master)

    def load_prev_window(self):
        self.load_window = Toplevel(self.master)
        Label(self.load_window, text='Enter id:').pack()
        entry = Entry(self.load_window)
        entry.pack()
        Button(self.load_window, text='Load!', command=lambda: self.load_prev(entry)).pack()


    def load_prev(self, entry):
        folders = os.listdir(file_path)
        folders = [f for f in folders if os.path.isdir(os.path.join(file_path, f))]
        hash_ = str(entry.get())
        for i in folders:
            if hash_ in i:
                messagebox.showinfo('Found!', 'Found folder %s.\n Loading the files in that folder here..' %i)
                global uniq_id
                global output_path
                uniq_id = hash_
                self.hash_var.set(hash_)
                print('Changed ID to %s' %hash_)
                output_path = os.path.join(file_path, i)
                self.load_window.destroy()
                return
        # if folder is not found,
        messagebox.showerror('Error', 'No folder with that name.\n The folder must exist in: \n %s' %file_path)
        

    def check_and_run(self, run=True):
        files = os.listdir(output_path)
        okay = True
        absentee = []
        file_list = ['simulation.xml', 'archetypes.xml', 'prototypes.xml',
                     'regions.xml', 'recipes.xml']
        for i in file_list:
            if i not in files:
                absentee.append(i.replace('.xml', ''))
        if len(absentee) != 0:
            string = 'You have not made the following blocks:\n'
            for abse in absentee:
                string += '\t' + abse + '\n'
            messagebox.showerror('Error', string)
            okay = False

        if okay:
            input_file = ''
            for i in file_list:
                skipfront = 0
                skipback = 0
                with open(os.path.join(output_path, i), 'r') as f:
                    x = f.readlines()
                    if 'prototype' in i:
                        skipfront += 1
                    if 'prototype' in i or 'region' in i or 'recipe' in i:
                        skipfront += 1
                        skipback -= 1
                    if skipback == 0:
                        lines = x[skipfront:]
                    else:
                        lines = x[skipfront:skipback]
                    input_file += ''.join(lines)
                    input_file += '\n\n\n'
            with open(os.path.join(output_path, 'input.xml'), 'w') as f:
                f.write(input_file)
            if run:
                try:
                    input_path = os.path.join(output_path, 'input.xml')
                    output = os.path.join(output_path, 'output.sqlite')
                    command = 'cyclus -o %s %s' %(output, input_path)
                    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
                    # check success
                except:
                    messagebox.showerror('Error', 'Cannot find Cyclus. Input file is rendered, though.')
            else:
                messagebox.showinfo('Success', 'Complete Cyclus input file rendered in %s' %os.path.join(output_path, 'input.xml'))
                self.master.destroy()

            # compile into one big file
            # run it
            # see if it turns successfully


    def guide(self):

        self.guide_window = Toplevel(self.master)
        self.guide_window.geometry('+0+0')
        guide_text = """
        Welcome!

        A Cyclus input file has 5 major blocks, with explanations:

        Simulation:
            Here, you define meta simulation parameters like
            startyear, timesteps, and decay methods.

        Archetypes:
            Since Cyclus is a modular framework, here you
            decide what libraries and what archetypes to use.
            An archetype is a self-contained code that defines
            a facility's behavior (e.g. reactor, sink)

            (A reactor archetype [takes in, depletes, and discharges fuel at a
             predefined cycle length])

        Prototypes:
            Here, you define the archetypes' parameters.
            You can define more than one prototype for one archetype.
            For example, you can have:
                reactor with 3 60-assembly batches with power 1000 MWe.
                reactor with 1 140-assembly batch with power 500 MWe.
            They both use the reactor archetype, but are different prototypes.

            This block is crucial, since you must set the in-and-out commodities
            of each prototype to match others' in-and-out commodity.
            For example, if you want the reactor to trade with the source,
            the outcommodity of the source prototype should match the
            incommodity of the reactor prototype, so they trade.

            ( The Clinton reactor prototype takes in, depletes and discharges
             fuel in [18-month cycles], outputs [1,062 MWe], and uses [UOX] fuel.) 

        Regions:
            Here, you actually set up how the prototypes will be `played'
            - when to enter, when to exit, and how many to play.

            (The Clinton reactor (prototype) is inside the Exelon Institution,
             which is inside the U.S.A. region, has 1 unit (n_build),
             has a lifetime of 960 months (lifetimes),
             and enters simulation in timestep 100 (build_times).)

        Recipes:
            Well, recipes, are, well, recipes.

            ( ???? )

        """
        Label(self.guide_window, text=guide_text, justify=LEFT).pack(padx=30, pady=30)



class SimulationWindow(Frame):
    """ This is the simulation window where it takes input from the user on
        simulation parameters and makes a Cyclus control box
        
        entry_dict looks like:
        key: criteria
        val: value
    """
    def __init__(self, master):
        self.master = Toplevel(master)
        self.frame = Frame(self.master)
        self.master.geometry('+600+200')
        self.guide()
        inputs = ['duration', 'startmonth', 'startyear', 'decay',
                  'explicit_inventory', 'explicit_inventory_compact',
                  'dt']
        for i, txt in enumerate(inputs):
            Label(self.master, text=txt).grid(row=(i))

        self.entry_dict = {}
        for row, txt in enumerate(inputs):
            self.entry_dict[txt] = Entry(self.master)
            self.entry_dict[txt].grid(row=row, column=1)

        # default values
        self.entry_dict['startyear'].insert(END, 2019)
        self.entry_dict['decay'].insert(END, 'lazy')
        self.entry_dict['dt'].insert(END, 2629846)
        self.entry_dict['explicit_inventory'].insert(END, 0)
        self.entry_dict['explicit_inventory_compact'].insert(END, 0)

        if os.path.isfile(os.path.join(output_path, 'simulation.xml')):
            self.read_xml()

        done_button = Button(self.master, text='Done', command=lambda: self.done())
        done_button.grid(row=len(inputs)+1, columnspan=2)

    def is_it_pos_integer(self, num):
        if float(num) % 1.0 != 0.0:
            return False
        if float(num)  < 0:
            return False
        return True

    def read_xml(self):
        with open(os.path.join(output_path, 'simulation.xml'), 'r') as f:
            xml_dict = xmltodict.parse(f.read())['control']
        for key, val in xml_dict.items():
            self.entry_dict[key].insert(END, val)


    def done(self):
        self.entry_dict = {key: val.get() for key, val in self.entry_dict.items()}

        # check input:
        if '' in self.entry_dict.values():
            messagebox.showerror('Error', 'You omitted some parameters')
        elif not self.is_it_pos_integer(self.entry_dict['startmonth']):
            messagebox.showeeror('Error', 'Start Month must be a positive integer')
        elif not self.is_it_pos_integer(self.entry_dict['startyear']):
            messagebox.showerror('Error', 'Start Year must be a positive integer')
        elif int(self.entry_dict['startmonth']) not in list(range(1,13)):
            messagebox.showeeror('Error', 'Month has to be number from 1 to 12')
        elif self.entry_dict['decay'] not in ['never', 'lazy', 'manual']:
            messagebox.showeerror('Error', 'Decay must be either never, lazy, or manual')
        elif not self.is_it_pos_integer(self.entry_dict['dt']):
            messagebox.showerror('Error', 'dt must be a positive integer')
        else:
            messagebox.showinfo('Success', 'Rendered Simulation definition into xml! :)')
            xml_string = '<control>\n'
            for key, val in self.entry_dict.items():
                xml_string+='\t<%s>%s</%s>\n' %(key, val, key)
            xml_string += '</control>\n'
            with open(os.path.join(output_path, 'simulation.xml'), 'w') as f:
                f.write(xml_string)

            self.master.destroy()

    def guide(self):

        self.guide_window = Toplevel(self.master)
        self.guide_window.geometry('+0+0')

        guide_string = """
        duration = Duration of the simulation in dt (default is month)

        startmonth = Starting month of the simulation [1-12]
        
        startyear = Starting year of the simulation
        
        decay = Decay solver [never, lazy, manual]
        
        explicit_inventory =  Create ExplicitInventory table [0,1]
       
        explicit_inventory_compact = Create ExplicitInventoryCompact table [0,1]
       
        dt = Duration of single timestep in seconds (default is a month -> 2,629,846)

        FOR MORE INFORMATION:
        http://fuelcycle.org/user/input_specs/control.html
        """
        Label(self.guide_window, text=guide_string, justify=LEFT).pack(padx=30, pady=30)




class ArchetypeWindow(Frame):
    def __init__(self, master):
        """
        arche looks like:
        array = []
        [0] = library
        [1] = archetype name
        """
        self.master = Toplevel(master)
        self.frame = Frame(self.master)
        self.master.geometry('+600+200')
        self.guide()
        self.arche = [['agents', 'NullInst'], ['agents', 'NullRegion'], ['cycamore', 'Source'],
                      ['cycamore', 'Sink'], ['cycamore', 'DeployInst'], ['cycamore', 'Enrichment'],
                      ['cycamore', 'FuelFab'], ['cycamore', 'GrowthRegion'], ['cycamore', 'ManagerInst'],
                      ['cycamore', 'Mixer'], ['cycamore', 'Reactor'], ['cycamore', 'Separations'],
                      ['cycamore', 'Storage']]
        try:
            path = os.path.join(output_path, 'm.json')
            command = 'cyclus -m > %s' %path
            process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
            with open(path, 'r') as f:
                jtxt = f.read()
            j = json.loads(jtxt)
            self.arche = j['specs']
            self.arche = [[q[0], q[1]] for q in (i[1:].split(':') for i in self.arche)]
        except:
            messagebox.showinfo('Cyclus not found', 'Cyclus is not found. Using all cyclus/cycamore arcehtypes as default.')
        self.default_arche = copy.deepcopy(self.arche)
        if os.path.isfile(os.path.join(output_path, 'archetypes.xml')): 
            self.read_xml()



        Button(self.master, text='Add Row', command= lambda : self.add_more()).grid(row=1)
        Button(self.master, text='Add!', command= lambda : self.add()).grid(row=2)
        Button(self.master, text='Default', command= lambda: self.to_default()).grid(row=3)
        Button(self.master, text='Done', command= lambda: self.done()).grid(row=4)
        Label(self.master, text='Library').grid(row=0, column=2)
        Label(self.master, text='Archetype').grid(row=0, column=3)
        self.entry_list = []
        self.additional_arche = []
        self.rownum = 1

        # status window
        self.status_window = Toplevel(self.master)
        Label(self.status_window, text='Loaded modules:').pack()
        self.status_var = StringVar()
        self.update_loaded_modules()
        Label(self.status_window, textvariable=self.status_var).pack()


    def update_loaded_modules(self):
        """ this functions updates the label object in the status window
            so the loaded archetypes are updated live"""
        string = ''

        for i in self.arche:
            string += i[0]+ ' :: ' + i[1] + '\n'
        self.status_var.set(string)

    def read_xml(self):
        new_arche = []
        with open(os.path.join(output_path, 'archetypes.xml'), 'r') as f:
            xml_dict = xmltodict.parse(f.read())['archetypes']
        for entry in xml_dict['spec']:
            new_arche.append([entry['lib'], entry['name']])
        self.arche = new_arche

    def add_more(self):
        row_list = []
        # library and archetype set
        row_list.append(Entry(self.master))
        row_list.append(Entry(self.master))
        row_list[0].grid(row=self.rownum, column=2)
        row_list[1].grid(row=self.rownum, column=3)
        self.entry_list.append(row_list)
        self.rownum += 1

    def to_default(self):
        self.arche = self.default_arche
        self.update_loaded_modules()

    def add(self):
        enter = [[x[0].get(), x[1].get()] for x in self.entry_list]
        dont_add_indx = []
        messed_up_indx = []
        err = False
        for indx,entry in enumerate(enter):
            if entry[0] == '' and entry[1] == '':
                dont_add_indx.append(indx)
            if entry[0] == '' and entry[1] != '':
                messed_up_indx.append(indx)
                err = True
        if len(dont_add_indx) == len(enter):
            messagebox.showerror('Error', 'You did not input any libraries. Click Done if you do not want to add more libraries.')
            return
        if err:
            message = 'You messed up on rows:\n'
            for indx in messed_up_indx:
                message += indx + '\t'
            messagebox.showerror('Error', message)
            return
        else:

            string = 'Adding %i new libraries' %(len(enter) - len(dont_add_indx))
            if len(dont_add_indx) != 0:
                string += '\n Ignoring empty rows: '
                for r in dont_add_indx:
                    string += r + '  '
            for indx, val in enumerate(enter):
                if indx in dont_add_indx:
                    continue
                self.arche.append(val)
            self.update_loaded_modules()


    def done(self):
        string = '<archetypes>\n'
        for pair in self.arche:
            string += '\t<spec>\t<lib>%s</lib>\t<name>%s</name></spec>\n' %(pair[0], pair[1])
        string += '</archetypes>\n'
        with open(os.path.join(output_path, 'archetypes.xml'), 'w') as f:
            f.write(string)
        self.master.destroy()

    def guide(self):

        self.guide_window = Toplevel(self.master)
        self.guide_window.geometry('+0+0')
        guide_string = """
        All Cyclus and Cycamore archetypes are already added. If there are additional archetypes
        you would like to add, click the `Add Row' button, type in the library and archetype,
        and press `Add!'. 

        If you made a mistake, you can go back to the default Cyclus + Cycamore
        archetypes by clicking `Default'.

        Once you're done, click `Done'.


        FOR MORE INFORMATION:
        http://fuelcycle.org/user/input_specs/archetypes.html
        """
        Label(self.guide_window, text=guide_string, justify=LEFT).pack(padx=30, pady=30)



class PrototypeWindow(Frame):
    def __init__(self, master):
        """
        proto_dict looks like:

        """
        self.master = Toplevel(master)
        self.frame = Frame(self.master)
        self.master.geometry('+600+200')
        self.guide()
        Label(self.master, text='Choose an archetype to add:').grid(row=0)
        self.get_schema()
        self.proto_dict = {}
        if os.path.isfile(os.path.join(output_path, 'prototypes.xml')):
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
        Label(self.status_window, text='Defined Archetypes:').pack()
        self.status_var = StringVar()
        self.status_var.set('')
        self.update_loaded_modules()
        Label(self.status_window, textvariable=self.status_var).pack()


    def get_schema(self):
        # get from cyclus -m
        path = os.path.join(output_path, 'm.json')
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
        with open(os.path.join(output_path, 'archetypes.xml'), 'r') as f:
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
        with open(os.path.join(output_path, 'prototypes.xml'), 'w') as f:
            for name, config in self.proto_dict.items():
                facility_dict = {}
                facility_dict['name'] = name
                facility_dict['config'] = config['config']
                new_dict['root']['facility'].append(facility_dict)
            print(self.proto_dict)
            print('\n\n')
            print(new_dict)
            f.write(xmltodict.unparse(new_dict, pretty=True))
        messagebox.showinfo('Sucess', 'Successfully rendered %i prototypes!' %len(new_dict['root']['facility']))
        self.master.destroy()



    def definition_window(self, *args):
        self.def_window = Toplevel(self.master)
        self.def_window.geometry('+800+400')
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
        print(self.proto_dict)
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
        print(string)
        t = Text(proto_guide_window_)
        t.pack()
        t.insert(END, string)


    def add_sep_stream(self):
        self.sep_stream_window = Toplevel(self.def_window)

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
        print(self.entry_dict)
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
        with open(os.path.join(output_path, 'prototypes.xml'), 'r') as f:
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
        print(self.proto_dict)


    def guide(self):

        self.guide_window = Toplevel(self.master)
        self.guide_window.geometry('+0+0')
        guide_text = """
        Here you define archetypes with specific parameters to use in the simulation.
        An archetype is the code (general behavior of facility - e.g. reactor facility )
        A prototype is an archetype + user-defined parameters 
        (e.g. reactor with 3 60-assembly batches and 1000MWe power output).

        Here you can add prototypes by taking an archetype template and defining
        your parameters.

        """
        Label(self.guide_window, text=guide_text, justify=LEFT).pack(padx=30, pady=30)



class RegionWindow(Frame):
    def __init__(self, master):
        """
        Region dict looks like:
        key: region name
        val: dictionary
            key: institution name
            val: array
                [0] prototype name
                [1] n_build
                [2] entertime
                [3] lifetime
        """

        self.master = Toplevel(master)
        self.frame = Frame(self.master)
        self.master.geometry('+600+200')
        self.load_prototypes()
        self.status_var = StringVar()
        self.guide()
        self.region_dict = {}
        Button(self.master, text='Add Region', command=lambda: self.add_region()).grid(row=0)


        if os.path.isfile(os.path.join(output_path, 'regions.xml')):
            self.read_xml()

        self.status_window = Toplevel(self.master)
        self.status_window.geometry('+800+400')
        Label(self.status_window, text='Current regions:').pack()
        
        self.update_region_status()
        Label(self.status_window, textvariable=self.status_var, justify=LEFT).pack()


    def load_prototypes(self):
        self.prototypes = []
        if os.path.isfile(os.path.join(output_path, 'prototypes.xml')):
            with open(os.path.join(output_path, 'prototypes.xml'), 'r') as f:
                xml_list = xmltodict.parse(f.read())['root']['facility']
                for facility in xml_list:
                    self.prototypes.append(facility['name'])
 
        else:
            return

    def read_xml(self):
        """
        read xml has wayy too many if else statements
        becasuse xmltodict reads single entries as strings
        while multiple entries as lists..
        """
        with open(os.path.join(output_path, 'regions.xml'), 'r') as f:
            xml_list = xmltodict.parse(f.read())['root']['region']
            if isinstance(xml_list, dict):
                xml_list = [xml_list]
            for region in xml_list:
                print('REGION', region)
                self.region_dict[region['name']] = {}
                if not isinstance(region['institution'], list):
                    do_it = 1
                else:
                    do_it = len(region['institution'])
                for i in range(do_it):
                    inst_array = []
                    if do_it == 1:
                        prototypes = region['institution']['config']['DeployInst']['prototypes']['val']
                        instname = region['institution']['name']
                    else:
                        prototypes = region['institution'][i]['config']['DeployInst']['prototypes']['val']
                        instname = region['institution'][i]['name']

                    if isinstance(prototypes, str):
                        entry_length = 1
                    else:
                        entry_length = len(prototypes)

                    for indx in range(entry_length):
                        entry_list = []
                        if do_it == 1:
                            entry_dict = region['institution']['config']['DeployInst']
                        else:
                            entry_dict = region['institution'][i]['config']['DeployInst']
                        for cat in ['prototypes', 'n_build', 'build_times', 'lifetimes']:
                            if entry_length == 1:
                                entry_list.append(entry_dict[cat]['val'])
                            else:
                                entry_list.append(entry_dict[cat]['val'][indx])
                        inst_array.append(entry_list)


                    self.region_dict[region['name']][instname] = inst_array

        self.update_region_status()

        # also get from the prototype file


    def add_region(self):
        # region name
        # add institution
        # finish button
        self.add_region_window = Toplevel(self.master)
        self.add_region_window.geometry('+800+300')
        Label(self.add_region_window, text='Region Name:').grid(row=0, column=0)
        region_name = Entry(self.add_region_window)
        region_name.grid(row=0, column=1)
        Button(self.add_region_window, text='Add Institution', command=lambda : self.add_inst(region_name.get())).grid(row=1, column=0)
        Button(self.add_region_window, text='Done', command=lambda : self.done_region()).grid(row=2, column=0)
        z = 0

    def done_region(self):
        if len(self.region_dict) == 0:
            messagebox.showerror('Error', 'No Regions were defined!')
            return
        self.compile_dict_to_xml()
        self.master.destroy()

    def compile_dict_to_xml(self):
        # name, institution
        region_template = '<region>\n\t<name>{name}</name>\n\t<config><NullRegion/></config>\n{institution}\n</region>\n'
        # name, deployinst
        inst_template = '\t<institution>\n\t\t<name>{name}</name>\n\t\t<config>\n\t\t\t<DeployInst>\n{deployinst}\n\t\t\t</DeployInst>\n\t\t</config>\n\t</institution>'
        val_template = '\t\t\t\t\t<val>{entry}</val>\n'
        string = '<root>\n'
        for regionname, inst_dict in self.region_dict.items():
            inst_chunk = ''
            for inst_name, inst_array in inst_dict.items():
                proto_string = '\t\t\t\t<prototypes>\n'
                n_build_string = '\t\t\t\t<n_build>\n'
                buildtime_string = '\t\t\t\t<build_times>\n'
                lifetime_string = '\t\t\t\t<lifetimes>\n'
                for entry in inst_array:
                    proto_string += val_template.format(entry=entry[0])
                    n_build_string += val_template.format(entry=entry[1])
                    buildtime_string += val_template.format(entry=entry[2])
                    lifetime_string += val_template.format(entry=entry[3])
                proto_string += '\t\t\t\t</prototypes>\n'
                n_build_string += '\t\t\t\t</n_build>\n'
                buildtime_string += '\t\t\t\t</build_times>\n'
                lifetime_string += '\t\t\t\t</lifetimes>\n'
                all_four = proto_string + n_build_string + buildtime_string + lifetime_string
                inst_chunk += inst_template.format(name=inst_name, deployinst=all_four)
            string += region_template.format(name=regionname, institution=inst_chunk)
        string += '\n</root>'
        with open(os.path.join(output_path, 'regions.xml'), 'w') as f:
            f.write(string)
        messagebox.showinfo('Success', 'Successfully rendered %i regions!' %len(self.region_dict))


    def add_inst(self, region_name):
        if region_name == '':
            messagebox.showerror('Error', 'You have to define the region name before adding and institution!')
            return
        self.add_inst_window = Toplevel(self.add_region_window)
        self.inst_dict = {}
        self.region_dict[region_name] = {}
        self.current_region = region_name
        Label(self.add_inst_window, text='Institution Name:').grid(row=0, column=1)
        inst_name_entry = Entry(self.add_inst_window)
        inst_name_entry.grid(row=0, column=2)
        Button(self.add_inst_window, text='Done', command= lambda : self.submit_inst(inst_name_entry.get())).grid(row=1, column=0)
        Label(self.add_inst_window, text='Add new prototypes here:').grid(row=2, columnspan=3)
        Button(self.add_inst_window, text='Add Row', command= lambda: self.add_inst_row()).grid(row=3, column=3)
        self.inst_entry_dict = {'prototypes': [], 'lifetimes': [],
                                'n_build': [], 'build_times': []}
        self.cat_list = ['prototypes', 'n_build', 'build_times', 'lifetimes']
        for indx, val in enumerate(self.cat_list):
            Label(self.add_inst_window, text=val).grid(row=4, column=indx)
            self.inst_entry_dict[val].append(Entry(self.add_inst_window))
            self.inst_entry_dict[val][-1].grid(row=5, column=indx)
        self.rownum = 6

        # show realtime institutions added

    def submit_inst(self, inst_name):
        # check input correctness:
        if inst_name == '':
            messagebox.showerror('Error', 'You have to define an Institution Name')
            return
        inst_array = []
        for indx in range(len(self.inst_entry_dict['prototypes'])):
            prototype_ = self.inst_entry_dict['prototypes'][indx].get()
            lifetime_ = self.inst_entry_dict['lifetimes'][indx].get()
            build_time_ = self.inst_entry_dict['build_times'][indx].get()
            n_build_ = self.inst_entry_dict['n_build'][indx].get()
            # skip missing rows
            if prototype_ == lifetime_ == build_time_ == n_build_ == '':
                continue
            # check if there are missing parameters
            elif '' in [prototype_, lifetime_, build_time_, n_build_]:
                messagebox.showerror('Error', 'You are missing a parameter for line %i' %indx)
                return
            # check if the ints are ints
            if not (self.check_if_int(lifetime_) & self.check_if_int(build_time_)
                    & self.check_if_int(n_build_)):
                messagebox.showerror('Error', 'Entertime, lifetime, and n_build have to be integers.')
                return
            inst_array.append([prototype_, n_build_, build_time_, lifetime_])
            
        if len(inst_array) == 0:
            messagebox.showerror('Error', 'There are no entries! ')
            return
        self.inst_dict[inst_name] = inst_array
        messagebox.showinfo('Added', 'Added institution %s' %inst_name)
        self.region_dict[self.current_region] = self.inst_dict
        self.update_region_status()


    def check_if_int(self, string):
        try:
            int(string)
            return True
        except ValueError:
            return False


    def add_inst_row(self):
        for indx, val in enumerate(self.cat_list):
            self.inst_entry_dict[val].append(Entry(self.add_inst_window))
            self.inst_entry_dict[val][-1].grid(row=self.rownum, column=indx)
        self.rownum += 1

    def update_region_status(self):
        print(self.region_dict)
        string = '\t\t\t\t\tN_build\tBuild Time\t Lifetime'
        for key, val in self.region_dict.items():
            string += '\n' + key + '\n'
            for key2, val2 in val.items():
                string += '\t-> ' + key2 + '\t\t\t' + '\t' + '\t' + '\n'
                for i in val2:
                    if i[0] not in self.prototypes:
                        i[0] += ' (x)'
                    string += '\t\t->> ' + i[0] + '\t\t' + i[1] +'\t' + i[2] + '\t' + i[3] + '\n'
        self.status_var.set(string)


    def close_window(self):
        self.master.destroy()

    def guide(self):

        self.guide_window = Toplevel(self.master)
        self.guide_window.geometry('+0+0')
        Label(self.guide_window, text='some helpful message').pack(padx=30, pady=30)



class RecipeWindow(Frame):
    """ Note: Recipes are generated with <root> parent node for xml for parsing reasons"""

    def __init__(self, master):
        self.master = Toplevel(master)
        self.frame = Frame(self.master)
        self.master.geometry('+600+200')
        self.guide()
        browse_button = Button(self.master, text='Add From File [atomic]', command=lambda : self.askopenfile('atom')).grid(row=1)
        browse_button = Button(self.master, text='Add From File [mass]', command= lambda : self.askopenfile('mass')).grid(row=2)
        Button(self.master, text='Add Recipe Manually [atomic]', command=lambda : self.add_recipe('atom')).grid(row=3)
        Button(self.master, text='Add Recipe Manually [mass]', command=lambda : self.add_recipe('mass')).grid(row=4)

        Button(self.master, text='Finish', command=lambda: self.done()).grid(row=6)
        self.recipe_dict = {}

        if os.path.isfile(os.path.join(output_path, 'recipes.xml')):
            self.read_xml()

        self.status_window = Toplevel(self.master)
        self.status_window.geometry('+800+400')
        Label(self.status_window, text='Loaded recipes:').pack()
        self.status_var = StringVar()
        self.update_loaded_recipes()
        Label(self.status_window, textvariable=self.status_var).pack()

    def update_loaded_recipes(self):
        string = ''
        for key in self.recipe_dict:
            string += key + '\n'
        self.status_var.set(string)


    def add_recipe(self, atom_or_mass):
        """
        Button add recipe will prompt user-input recipe name and text
        """
        self.addrecipe_window = Toplevel(self.master)
        self.addrecipe_window.geometry('+800+400')

        Button(self.addrecipe_window, text='Done!',
               command= lambda : self.send_input(name_entry, textfield, self.addrecipe_window, atom_or_mass)).grid(row=0, columnspan=2)
        Label(self.addrecipe_window, text='Recipe name').grid(row=1, column=0)
        name_entry = Entry(self.addrecipe_window)
        name_entry.grid(row=1, column=1)
        Label(self.addrecipe_window, text='Recipe:').grid(row=2, columnspan=2)
        textfield = ScrolledText(self.addrecipe_window, wrap=WORD)
        textfield.grid(row=3, columnspan=2)


    def send_input(self, name, text, window, atom_or_mass):
        """
        Gets the entry and scrolltext objects and obtains the actual data
        and sends it to recipe_input for testing and storage.
        """
        name = name.get() + '_' + atom_or_mass
        text = str(text.get(1.0, END))
        self.recipe_input(name, text, window)

    def read_xml(self):
        with open(os.path.join(output_path, 'recipes.xml'), 'r') as f:
            xml_list = xmltodict.parse(f.read())['root']['recipe']
            for recipe in xml_list:
                comp_dict = {}
                for entry in recipe['nuclide']:
                    for iso, comp in entry.items():
                        comp_dict[iso] = comp
                self.recipe_dict[recipe['name']] = {'base': recipe['basis'],
                                                    'composition': comp_dict}
                print('Printing the nuclide part')
                print(recipe['nuclide'])

        print('Final')
        print(self.recipe_dict)


    def recipe_input(self, name, text, window):
        if name == '' or text == '':
            messagebox.showerror('Name or text missing! :(')
            return
        if name.split('_')[-1] not in ['atom', 'mass']:
            raise ValueError('Something Wrong man, either has to have _atom or _mass appended')
        base = name.split('_')[-1]
        print(base)
        name = name.replace('_'+base, '')


        # check input
        # if it recognizes a comma, then we are going to
        # look at it as a csv file
        # if not, its just the plaintext format
        if ',' in text:
            text = text.replace(',', ' ')    
        composition_dict = self.parse_plaintext(text)


        if composition_dict == None:
            messagebox.showerror('Error', 'The recipe text is malformed! :( ')
            return


        self.recipe_dict[name] = {'base': base,
                                  'composition': composition_dict}
        # if not good, error message
        # if good, kill window
        messagebox.showinfo('Recipe Saved', 'Recipe %s is saved!' %name)
        if window != None:
            window.destroy()
        self.update_loaded_recipes()    


    def parse_plaintext(self, text):
        print(text)
        composition_dict = {}
        for row in text.split('\n'):
            if row == '':
                continue
            print('row', row)
            e = row.split()
            print('split', e)
            composition_dict[e[0]] = float(e[1])        
        return composition_dict


    def askopenfile(self, base):
        file = filedialog.askopenfile(parent=self.master, mode='r', title='Choose a file')
        filename = os.path.splitext(os.path.basename(file.name))[0] + '_' + base
        data = file.read()
        print('filename', filename)
        print('data', data)
        
        self.recipe_input(filename, data, None)


    def done(self):
        string = '<root>\n'
        if len(self.recipe_dict.keys()) == 0:
            messagebox.error('Error', 'There are no recipes to output :(')
            return
        temp = '<recipe>\n\t<name>{name}</name>\n\t<basis>{base}</basis>\n{recipe}</recipe>\n'
        comp_string = ''
        for key in self.recipe_dict:
            for iso, comp in self.recipe_dict[key]['composition'].items():
                comp_string += '\t<nuclide>\t<id>%s</id>\t<comp>%f</comp>\t</nuclide>\n' %(iso, comp)
            name = key
            base = self.recipe_dict[key]['base']
            string += temp.format(name=name,
                                  base=base,
                                  recipe=comp_string)
            string += '\n'
        string += '</root>'
        with open(os.path.join(output_path, 'recipes.xml'), 'w') as f:
            f.write(string)
        messagebox.showinfo('Success', 'Successfully rendered %i recipes! :)' %len(self.recipe_dict.keys()))
        self.master.destroy()

    def guide(self):
        self.guide_window = Toplevel(self.master)
        self.guide_window.geometry('+0+0')
        guide_string = """
        ** Currently, you can only add one recipe at a time (future work)

        The format of recipes could be comma, space, or tab separated.
        For example:
        92235 0.7
        92238 99.3
        OR
        92235, 0.7
        92238, 99.3
        OR
        92235   0.7
        92238   99.3

        Note:
        1. The compositions are automatically normalized by Cyclus :)
        2. Acceptable formats for isotope symbols are:
            ZZAAA, ZZAAASSSS, name (e.g. Pu-239, Pu239, pu-239)
        """
        Label(self.guide_window, text=guide_string, justify=LEFT).pack(padx=30, pady=30)



root = Tk()
root.geometry('400x300')
app = Cygui(root)
root.mainloop()




