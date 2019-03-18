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
        

    def check_and_run(self):
        files = os.listdir(output_path)
        okay = True
        absentee = []
        for i in ['simulation.xml', 'archetype.xml', 'prototype.xml',
                  'regions.xml', 'recipe.xml']:
            if i not in files:
                absentee.append(i.replace('.xml', ''))
        if len(absentee) != 0:
            string = 'You have not made the following blocks:\n'
            for abse in absentee:
                string += '\t' + abse + '\n'
            messagebox.showerror('Error', string)
            okay = False

        if okay:
            print('I am okay')
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
        self.proto_dict = {}
        self.tag_dict = {}
        if os.path.isfile(os.path.join(output_path, 'prototypes.xml')):
            self.read_xml()
        self.load_archetypes()

        self.tkvar = StringVar(self.master)
        archetypes = [x[0] + ':' + x[1] for x in self.arches]
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
            # this is disabled to save space
            #self.config_string = ''
            #self.dig_dict(val['config'])
            #string += self.config_string + '\n'
        self.status_var.set(string)


    def submit(self):
        new_dict = {'root': {'facility': []}}
        with open(os.path.join(output_path, 'prototypes.xml'), 'w') as f:
            for name, config in self.proto_dict.items():
                facility_dict = {}
                facility_dict['name'] = name
                facility_dict['config'] = {config['archetype']: config['config']}
                new_dict['root']['facility'].append(facility_dict)
            f.write(xmltodict.unparse(new_dict, pretty=True))
        messagebox.showinfo('Sucess', 'Successfully rendered %i prototypes!' %len(new_dict['root']['facility']))
        self.master.destroy()

    def dig_dict(self, dictionary, pretab=0, indent=0):
        self.config_string = ''
        for key, val in dictionary.items():
            self.config_string += '\t'*(pretab + indent) + str(key) + '\n'
            if isinstance(val, dict):
                self.dig_dict(val, indent+1)
            else:
                self.config_string += '\t'*(pretab + indent+1) + str(val) + '\n'


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
                    val_list = {'val': val_list}
                    
                else:
                    val_list = val_list.get()
                    if val_list == '':
                        continue
                # check for empty values    
                config_dict[archetype_name][param] = val_list
        
        self.proto_dict[proto_name] = {'archetype': archetype_name,
                                       'config': config_dict}
        messagebox.showinfo('Success', 'Successfully created %s prototype %s' %(archetype_name, proto_name))
        print(self.proto_dict)
        self.update_loaded_modules()
        self.def_window.destroy()


    def def_entries(self, archetype):
        start_row = 2
        self.entry_dict = {}
        """
        entry_dict:
        key: name of entry (e.g. cycle_time)
        val: dict
            key: rownum
            val: entry object list (length = column no.)
        # did not do matrix since the column lengths can be irregular
        """
        if archetype == 'cycamore:Reactor':
            oneormore = ['fuel_incommods', 'fuel_inrecipes', 'fuel_prefs*', 'fuel_outcommods',
                        'fuel_outrecipes', 'recipe_change_times*', 'recipe_change_commods*',
                        'recipe_change_in*', 'recipe_change_out*', 'pref_change_times*',
                        'pref_change_commods*', 'pref_change_values*']
            one = ['assem_size', 'n_assem_batch', 'n_assem_core', 'n_assem_fresh*',
                   'n_assem_spent*', 'cycle_time', 'refuel_time', 'cycle_step*', 'power_cap',
                   'power_name*']
        

        if archetype == 'cycamore:Source':
            one = ['outcommod', 'outrecipe*', 'inventory_size*', 'throughput*']
            oneormore = []


        if archetype == 'cycamore:Sink':
            oneormore = ['in_commods', 'in_commod_prefs*'] 
            one = ['recipe_name*', 'max_inv_size*', 'capacity*']

        if archetype == 'cycamore:Enrichment':
            oneormore = []
            one = ['feed_commod', 'feed_recipe', 'product_commod', 'tails_commod', 'tails_assay*',
                   'initial_feed*', 'max_feed_inventory*', 'max_enrich*', 'order_prefs*' , 'swu_capacity*']

        if archetype == 'cycamore:Separations':
            oneormore = ['feed_commods', 'feed_commod_prefs*', ]
            one = ['feed_recipe*', 'feedbuf_size', 'throughput*', 'lefover_commod*', 'leftoverbuf_size*']
            # add stream button
            # start_row += 1
            # Button(self.def_window, )

        if archetype == 'cycamore:FuelFab':
            oneormore = ['fill_commods', 'fill_commod_prefs*', 'fiss_commods', 'fiss_commod_prefs*']
            one = ['fill_recipe','fill_size', 'fiss_recipe', 'fiss_size', 'topup_cmomod*', 'topup_pref*',
                   'topup_recipe*', 'topup_size*', 'outcommod', 'throughput*', 'spectrum']
            # discrete choice for spectrum


        if archetype == 'cycamore:Storage':
            oneormore = []
            one = []

        if archetype == 'cycamore:Enrichment':
            oneormore = []
            one = []





        start_row += 1
        self.add_row_oneormore(val, self.def_window, start_row)
        self.add_rwo(val, self.def_window, start_row)   
            # add color for non-essential parameters


    def source_def(self):
        start_row = 2
        self.entry_dict = {}
        


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
                facility_name = facility['name']
                archetype = list(facility['config'].keys())[0]
                self.proto_dict[facility_name] = {'archetype': archetype,
                                                  'config': facility['config'][archetype]}
        print(self.proto_dict)


    def render_xml(self):
        z= 0

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
        Label(self.master, text='You can upload a csv or plaintext').grid(row=0)
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




