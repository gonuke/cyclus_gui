from tkinter import *
from tkinter import messagebox
from tkinter import filedialog
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
import xmltodict
import uuid
import os
import shutil
import json
import copy
from cyclus_gui.gui.sim_window import SimulationWindow
from cyclus_gui.gui.arche_window import ArchetypeWindow
from cyclus_gui.gui.proto_window import PrototypeWindow
from cyclus_gui.gui.region_window import RegionWindow
from cyclus_gui.gui.recipe_window import RecipeWindow
from cyclus_gui.gui.backend_window import BackendWindow
import subprocess
import copy
from cyclus_gui.gui.run_cyclus import cyclus_run
import cyclus_gui.tools.from_pris as fp
import cyclus_gui.tools.pris_data as pris_data
from cyclus_gui.gui.hovertip import CreateToolTip
from cyclus_gui.gui.window_tools import *
import platform

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import networkx as nx

os_ = platform.system()
print('Your OS is:', os_)
if 'windows' in os_.lower():
    windows=True
else:
    windows=False


uniq_id = str(uuid.uuid4())[:3]
file_path = os.path.abspath('.')


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
        self.file_list = ['control.xml', 'archetypes.xml', 'facility.xml',
                          'region.xml', 'recipe.xml']
        self.master = master
        # self.master.geometry('+0+0')
        
        self.init_window()
        self.uniq_id = uniq_id
        
        print('Your screen resolution is:')
        self.screen_width = master.winfo_screenwidth()
        self.screen_height = master.winfo_screenheight()
        print(self.screen_width, self.screen_height)
        self.guide()


    def init_window(self):
        self.master.title('GUI')

        # menu instance
        menu = Menu(self.master)
        self.initialized = {}
        # self.master.config(menu=menu)


        self.hash_var = StringVar()
        self.hash_var.set(uniq_id)

        columnspan=5
        q = Label(root, text='Cyclus Helper', bg='yellow')
        q.grid(row=0, column=2)
        CreateToolTip(q, text='you found the secret\n hover tip \n huehuehuehue')

        Label(root, text='').grid(row=1, column=0, columnspan=2)
        Label(root, textvariable=self.hash_var, bg='pale green').grid(row=1, column=2)
        saveas_button = Button(root, text='Save as', command=lambda:self.save_as(), highlightbackground='blue')
        saveas_button.grid(row=1, column=columnspan-1)

        Label(root, text='==========================').grid(row=2, column=0, columnspan=columnspan)
        
        Label(root, text='Generate / Edit Blocks').grid(row=3, column=0)
        Label(root, text='=============').grid(row=4, column=0)
        Label(root, text='Load:').grid(row=3, column=2)
        Label(root, text='=============').grid(row=4, column=2)
        Label(root, text='Run / Visualize').grid(row=3, column=4)
        Label(root, text='=============').grid(row=4, column=4)


        sim_button = Button(root, text='Simulation', command=lambda : self.open_window('simulation', output_path))
        sim_button.grid(row=5, column=0)

        library_button = Button(root, text='Libraries', command=lambda : self.open_window('archetype', output_path))
        library_button.grid(row=6, column=0)

        prototype_button = Button(root, text='Facilities', command=lambda : self.open_window('facility', output_path))
        prototype_button.grid(row=7, column=0)

        region_button = Button(root, text='Regions', command=lambda : self.open_window('region', output_path))
        region_button.grid(row=8, column=0)

        recipe_button = Button(root, text='Recipes', command=lambda : self.open_window('recipe', output_path))
        recipe_button.grid(row=9, column=0)

        for i in range(5,10):
            Label(root, text='   ').grid(row=i, column=1)
            Label(root, text='   ').grid(row=i, column=3)

        load_button = Button(root, text='From Instance', command=lambda: self.load_prev_window())
        load_complete_input = Button(root, text='From xml', command=lambda: self.askopenfile())
        load_pris = Button(root, text='From PRIS', command=lambda: self.load_from_pris())
        view_input_button = Button(root, text='View Input', command=lambda: self.xml_window())
        make_input_button = Button(root, text='Generate Input', command=lambda: self.check_and_run(run=False))
        combine_run_button = Button(root, text='Combine and Run', command= lambda: self.check_and_run())
        backend_button = Button(root, text='Backend Analysis', command= lambda: self.open_window('backend', output_path))
        
        if not windows:
            CreateToolTip(saveas_button, text='You can save your current instance with a different three-letter hash.')
            CreateToolTip(load_button, text='You can load from a previous instance.\nFor every instance, the GUI automatically creates `output_xxx` directory\nwhere it saves all the files, so that it can be called later on.')
            CreateToolTip(load_complete_input, text='You can load from a previously-existing Cyclus input xml file.\nThere are limitations to some input files, if they use special archetypes. You can edit or run cyclus on the file!')
            CreateToolTip(load_pris, text='You can initialize a simulation to a real-world initial condition!\nUsing this method the real-life fleet is automatically generated from the\nIAEA Power Reactor Information System (PRIS) database.')
            CreateToolTip(view_input_button, text='See the input in a window, just to see\nwhat it looks like.')
            CreateToolTip(make_input_button, text='Compile the input (into `input.xml`)\nbut not run the file')
            CreateToolTip(combine_run_button, text='You can compile and run this simulation\nYou can do this locally if you have a local installation of Cyclus\nBut you can also run it remotely.')
            CreateToolTip(backend_button, text='After getting the output file, you can get plots and csv files\nwith ease using this module.')

        load_button.grid(row=6, column=2)
        load_complete_input.grid(row=7, column=2)
        load_pris.grid(row=8, column=2)
        view_input_button.grid(row=5, column=4)
        make_input_button.grid(row=6, column=4)
        combine_run_button.grid(row=7, column=4)
        backend_button.grid(row=8, column=4)
    

    def open_window(self, name, output_path):
        if name == 'simulation':
            self.app = SimulationWindow(self.master, output_path)
        if name == 'archetype':
            self.app = ArchetypeWindow(self.master, output_path)
        if name == 'facility':
            if not os.path.isfile(os.path.join(output_path, 'archetypes.xml')):
                messagebox.showerror('Error', 'You must define the Archetype libraries first!')
                return
            self.app = PrototypeWindow(self.master, output_path)
        if name == 'region':
            self.app = RegionWindow(self.master, output_path)
        if name == 'recipe':
            self.app = RecipeWindow(self.master, output_path)
        if name == 'backend':
            if not os.path.isfile(os.path.join(output_path, 'cyclus.sqlite')):
                messagebox.showerror('Error', 'You must have the output file first!')
            else:
                self.app = BackendWindow(self.master, output_path)



    def save_as(self):
        self.saveas_window = Toplevel(self.master)
        self.saveas_window.title('Save as new three-letter hash')
        Label(self.saveas_window, text='Enter new three-letter hash:', bg='yellow').pack()
        entry = Entry(self.saveas_window)
        entry.pack()
        Button(self.saveas_window, text='Save as!', command=lambda:self.save_as_exec(entry)).pack()

    def save_as_exec(self,entry):
        new_hash = str(entry.get())
        if os.path.isdir('output_' + new_hash):
            messagebox.showerror('Already exists', 'Folder output_%s already exists!\n Try a different hash' %new_hash)
            return
        else:
            global uniq_id
            global output_path
            shutil.copytree(output_path, os.path.join(os.path.dirname(output_path), 'output_'+new_hash))
            messagebox.showinfo('Success', 'Saved as new hash %s.\nYour current working instance has been changed from %s to %s' %(new_hash, uniq_id, new_hash))
            uniq_id = new_hash
            self.hash_var.set(new_hash)
            print('Changed ID to %s' %new_hash)
            output_path = os.path.join(file_path, 'output_'+new_hash)
            self.saveas_window.destroy()
            self.uniq_id = new_hash
            return


    def load_prev_window(self):
        try:
            if self.initialized['prev']:
                return
        except:
            z = 0

        self.initialized['prev'] = True
        self.load_window = Toplevel(self.master)
        self.load_window.title('Load previous with hash')
        folders = os.listdir(file_path)
        folders = [f for f in folders if os.path.isdir(os.path.join(file_path, f))]
        folders = [f for f in folders if 'output_' in f]
        hashs = [f.replace('output_', '') for f in folders]
        hashs = sorted([f for f in hashs if f != self.uniq_id])
        Label(self.load_window, text='Current working directory:').pack()
        Label(self.load_window, text=os.path.abspath(file_path), bg='yellow').pack()
        Label(self.load_window, text='Available instances:').pack()
        for h in hashs:
            Button(self.load_window, text=h, command=lambda:self.load_prev(h)).pack()
        if not hashs:
            # if list is empty:
            Label(self.load_window, text='NONE', bg='red').pack()


    def load_prev(self, h):
        files_in = os.listdir(os.path.join(file_path, 'output_%s'%h))
        info_text = 'Found folder output_%s.\nLoading input blocks:\n\n' %h
        for f_ in files_in:
            f_ = f_.replace('.xml', '')
            info_text += '\t%s\n' %f_
        messagebox.showinfo('Found!', info_text)
        global uniq_id
        global output_path
        uniq_id = h
        self.hash_var.set(h)
        print('Changed ID to %s' %h)
        output_path = os.path.join(file_path, 'output_%s' %h)
        self.load_window.destroy()
        shutil.rmtree('output_%s' %self.uniq_id)
        self.uniq_id = h
        self.initialized['prev'] = False
        return


    def askopenfile(self):
        file = filedialog.askopenfile(parent=self.master, mode='r', title='Choose an xml file')
        if not file:
            return
        self.load_xml_file(file)
        messagebox.showinfo('Successfully loaded file', 'Successfully loaded file')
        # self.load_xml_window.destroy()


    def load_xml_file(self, file):
        xml_dict = xmltodict.parse(file.read())['simulation']
        # check if file is good:
        elements = ['control', 'archetypes', 'facility', 'region', 'recipe']
        if list(xml_dict.keys()) != elements:
            messagebox.showerror('Error', 'This is a malformed xml file! Check file to see if it has all the nodes:\nIt needs:\n%s\n\nBut it only has:\n %s' %(', '.join(elements), ', '.join(list(xml_dict.keys()))))

        for part in elements:
            with open(os.path.join(output_path, part+'.xml'), 'w') as f:
                if part in ['facility', 'region', 'recipe']:
                    f.write('\n<root>')
                f.write(xmltodict.unparse({part: xml_dict[part]}, pretty=True, full_document=False))
                if part in ['facility', 'region', 'recipe']:
                    f.write('\n</root>')


    def load_from_pris(self):
        guide_text = """
You can `initialize' your simulation as a real-life nation!
This method loads from the PRIS database and deploys reactors in your
desired country, in a desired initial time. The reactor lifetimes
are calculated as a remaining lifetime.

Assumptions:
1. Timestep is assumed to be a month
2. Reactors below 100 MWe are filtered out (assumed to be research reactors)
3. Core size is linearly scaled with power capacity
4. Reactor lifetimes are all assumed to be 60 years from their first criticality date
5. Fuel Cycle facilities are deployed with infinite capacity.

Simulation defaults:
1. Reactors are cycamore::Reactor (recipe reactors)
2. By default deploys a `RandLand' region with `Fuel_Cycle_Facilities' institution with facilities:
   a. `nat_u_source' -> [natl_u]
   b. [natl_u] -> `enrichment' -> [uox]
   d. [uox_waste, used_candu, mox_waste, tailings, reprocess_waste] -> `SomeSink'
        """
        self.guide(guide_text)
        try:
            if self.initialized['pris']:
                return
        except:
            z=0

        self.initialized['pris'] = True
        self.load_from_pris_window = Toplevel(self.master)
        self.load_from_pris_window.geometry('+0+%s' %(int(self.screen_height/3)))
        self.entry_dict = {}
        self.load_from_pris_window.title('Load from PRIS database')
        Label(self.load_from_pris_window, text='Load existing fleets using the PRIS database').grid(row=0, columnspan=2)
        
        Label(self.load_from_pris_window, text='initial date (YYYYMMDD)').grid(row=1, column=0)
        self.entry_dict['initial_date'] = Entry(self.load_from_pris_window)
        self.entry_dict['initial_date'].grid(row=1, column=1)

        Label(self.load_from_pris_window, text='duration (Timesteps)').grid(row=2, column=0)
        self.entry_dict['duration'] = Entry(self.load_from_pris_window)
        self.entry_dict['duration'].grid(row=2, column=1)
        self.select_countries()

        Label(self.load_from_pris_window, text=' ').grid(row=4, columnspan=2)
        Button(self.load_from_pris_window, text='Done', command=lambda: self.gen_pris()).grid(row=5, columnspan=2)



    def select_countries(self):
        self.pris_csv_path = os.path.join(output_path, 'pris.csv')
        #print('PRIS CSV PATH')
        #print(self.pris_csv_path)
        #with open(self.pris_csv_path, 'r') as f:
        #    q = f.readlines()
        q = pris_data.pris_data().split('\n')
        with open(self.pris_csv_path, 'w') as f:
            f.write('\n'.join(q))
        country_list = sorted(list(set([w.split(',')[0] for w in q if 'Country' not in w])))
        self.country_select_window = Toplevel(self.load_from_pris_window)
        self.country_select_window.geometry('+%s+0' %(int(self.screen_width/4.5)))
        self.country_select_window.title('Select Countries')
        parent = assess_scroll_deny(len(country_list), self.country_select_window)
        self.selected_countries = []
        # get lists of countries
        Label(parent, text='Click on country to select:').grid(row=0, column=0)
        self.button_color = {}
        self.button_loc = {}
        for indx, c in enumerate(country_list):
            self.button_color[c] = Button(parent, text=c, command=lambda country=c : self.add_country(country, parent), fg='black')
            self.button_color[c].grid(row=indx+1, column=0)
            self.button_loc[c] = indx+1


    def add_country(self, country, parent):
        if country in self.selected_countries:
            self.selected_countries.remove(country)
            self.button_color[country] = Button(parent, text=country, command=lambda country=country: self.add_country(country, parent), fg='black').grid(row=self.button_loc[country], column=0)
        else:
            self.selected_countries.append(country)
            self.button_color[country] = Button(parent, text=country, command=lambda country=country: self.add_country(country, parent), fg='green', foreground='green').grid(row=self.button_loc[country], column=0)


    def gen_pris(self):
        if len(self.selected_countries) == 0 or len(self.entry_dict['initial_date'].get()) == 0 or len(self.entry_dict['duration'].get()) == 0:
            messagebox.showerror('You missed something', ' You need to select at least one country and fill out the dates')
        else:    
            init_date = int(self.entry_dict['initial_date'].get())
            duration = int(self.entry_dict['duration'].get())
            outpath = os.path.join(output_path, 'input.xml')
            fp.main(self.pris_csv_path, init_date, duration, self.selected_countries,
                    output_file=outpath)
            self.load_xml_file(open(outpath, 'r'))
            messagebox.showinfo('Successfully loaded file',
                                'Successfully loaded file with countries\n\n'+'\n'.join(self.selected_countries)+'\n See the flowchart for commodity and facility default definitions.')
            self.load_from_pris_window.destroy()
            self.pris_flowchart()
            

        self.initialized['pris'] = False


    def pris_flowchart(self):
        G = nx.DiGraph()
        natu = 'nat_u_source'
        enrichment = 'enrichment'
        reactors = 'Reactors\n(various names)'
        somesink = 'somesink'
        natl_u = 'natl_u\n[natl_u_recipe]'
        uox = 'uox\n[uox_fuel_recipe]'
        uox_waste = 'uox_waste\n[uox_used_fuel_recipe]'
        tailings = 'tailings\n(0.3% U235)'

        fac_color = '#d9fbd0'
        com_color = '#fbd5d0'

        G.add_node(natu, pos=(0,0), color=fac_color)
        G.add_node(enrichment, pos=(6, 6), color=fac_color)
        G.add_node(reactors, pos=(12, 12), color=fac_color)
        G.add_node(somesink, pos=(18, 18), color=fac_color)
        G.add_node(natl_u, pos=(3,3), color=com_color)
        G.add_node(uox, pos=(9,9), color=com_color)
        G.add_node(uox_waste, pos=(15,15), color=com_color)
        G.add_node(tailings, pos=(6,16), color=com_color)

        G.add_edge(natu, natl_u)
        G.add_edge(natl_u, enrichment)
        G.add_edge(enrichment, uox)
        G.add_edge(uox, reactors)
        G.add_edge(reactors, uox_waste)
        G.add_edge(uox_waste, somesink)
        G.add_edge(enrichment, tailings)
        G.add_edge(tailings, somesink)

        node_colors = list(nx.get_node_attributes(G, 'color').values())
        pos = nx.get_node_attributes(G, 'pos')

        f = plt.figure(1, figsize=(8, 8))
        ax = f.add_subplot(1,1,1)
        ax.scatter([0], [0], c=fac_color, label='Facility')
        ax.scatter([0], [0], c=com_color, label='Commodity [recipe]')

        nx.draw(G, pos, with_labels=True, node_color=node_colors, ax=ax, node_size=900)
        plt.legend(loc='lower right')
        plt.show()
        

    def check_and_run(self, run=True):
        files = os.listdir(output_path)
        okay = True
        absentee = []
        
        for i in self.file_list:
            if i not in files:
                absentee.append(i.replace('.xml', ''))
        if len(absentee) != 0:
            string = 'You have not made the following blocks:\n'
            for abse in absentee:
                string += '\t' + abse + '\n'
            messagebox.showerror('Error', string)
            okay = False

        if okay:
            input_file = '<simulation>\n'
            for i in self.file_list:
                skipfront = 0
                skipback = 0
                with open(os.path.join(output_path,i), 'r') as f:
                    x = f.read()
                    x = x.replace('<root>', '')
                    x = x.replace('</root>', '')
                    if i == 'archetypes.xml' and 'DeployInst' not in x:
                        x = x.replace('</archetypes>', """\t<spec>
        <lib>cycamore</lib>
        <name>DeployInst</name>
    </spec>
</archetypes>""")
                    input_file += x + '\n\n'
                """
                with open(os.path.join(output_path, i), 'r') as f:
                    x = f.readlines()
                    if 'facility' in i:
                        skipfront += 1
                    if 'facility' in i or 'region' in i or 'recipe' in i:
                        skipfront += 1
                        skipback -= 1
                    if skipback == 0:
                        lines = x[skipfront:]
                    else:
                        lines = x[skipfront:skipback]
                    input_file += ''.join(lines)
                    input_file += '\n\n\n'
                """
            input_file += '\n</simulation>'
            with open(os.path.join(output_path, 'input.xml'), 'w') as f:
                f.write(input_file)
            if run:                
                input_path = os.path.join(output_path, 'input.xml')
                output = os.path.join(output_path, 'cyclus.sqlite')
                run = cyclus_run(self.master, input_path, output)
            else:
                messagebox.showinfo('Success', 'successfully rendered input.xml')


    def guide(self, guide_text=''):
        self.guide_window = Toplevel(self.master)
        self.guide_window.title('Guide')
        if guide_text != '':
            self.guide_window.geometry('+%s+0' %(int(self.screen_width/1.5)))
        else:
            self.guide_window.geometry('+%s+0' %int(self.screen_width//2))
                
        if guide_text == '':
            guide_text = """
Welcome!

I am the guide window, and I will guide you
through the intricacies of Cyclus!

A Cyclus input file has 5 major blocks.
It is recommended you fill them out sequentially:

Simulation:
    Here, you define simulation parameters like
    startyear, timesteps, and decay methods.

Libraries:
    Since Cyclus is a modular framework, here you
    decide what libraries and what archetypes to use.
    An archetype is a self-contained code that defines
    a facility's behavior (e.g. reactor, sink). It is 
    automatically populated, so don't do anything
    unless you need some specific library.

    (A reactor archetype [takes in, depletes, and discharges fuel at a
     predefined cycle length])


Facilities:
    Here, you define the facilities' parameters.
    You can define more than one facility for one archetype.
    For example, you can have:
        reactor with 3 60-assembly batches with power 1000 MWe.
        reactor with 1 140-assembly batch with power 500 MWe.
    They both use the reactor archetype, but are different facilities.

    This block is crucial, since you must set the in-and-out commodities
    of each facility to match others' in-and-out commodity.
    For example, if you want the reactor to trade with the source,
    the out-commodity of the source facility should match the
    in-commodity of the reactor facility, so they trade.

    ( The Clinton reactor facility takes in, depletes and discharges
     fuel in [18-month cycles], outputs [1,062 MWe], and uses [UOX] fuel.) 

Regions:
    Here, you actually set up how the facility prototypes will be `played'
    - when to enter, when to exit, and how many to play.

    (The Clinton reactor (facility prototype) is inside the Exelon Institution,
     which is inside the U.S.A. region, has 1 unit (n_build),
     has a lifetime of 960 months (lifetimes),
     and enters simulation in timestep 100 (build_times).)


Recipes:
    Recipes are predefined compositions of various material. They can
    be defined as mass or atomic concentrations. You can import them
    from a CSV file or manually write them yourself.


All feedback and comments / bug reports can be made to baej@ornl.gov
Enjoy :)

            """
        st = ScrolledText(master=self.guide_window,
                          wrap=WORD)
        st.pack()
        st.insert(INSERT, guide_text)
        #Label(self.guide_window, text=guide_text, justify=LEFT).pack(padx=30, pady=30)


    def xml_window(self):
        try:
            self.xml_window_.destroy()
        except:
            t=0

        self.xml_window_ = Toplevel(self.master)
        self.xml_window_.title('XML rendering')
        self.xml_window_.geometry('+350+0')

        tab_parent = ttk.Notebook(self.xml_window_)
        file_paths = [os.path.join(output_path, x) for x in self.file_list]
        tab_dict = {}
        for indx, file in enumerate(file_paths):
            key = self.file_list[indx].replace('.xml', '')
            tab_dict[key] = Frame(tab_parent)
            tab_parent.add(tab_dict[key], text=key)
            #tab_dict[key] = assess_scroll_deny(100, tab_dict[key])
            st = ScrolledText(master=tab_dict[key], wrap=WORD, width=100, height=30)
            st.pack()

            #q = Text(tab_dict[key], width=100, height=30)
            #q.pack()
            if os.path.isfile(file):
                with open(file, 'r') as f:
                    s = f.read().replace('<root>', '').replace('</root>', '')
            else:
                s = '-- file does not exist --'
            st.insert(INSERT, s)

            #q.insert(END, s)

        tab_parent.pack(expand=1, fill='both')




root = Tk()
app = Cygui(root)
root.mainloop()




