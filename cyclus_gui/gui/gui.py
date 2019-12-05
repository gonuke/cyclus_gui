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
from sim_window import SimulationWindow
from arche_window import ArchetypeWindow
from proto_window import PrototypeWindow
from region_window import RegionWindow
from recipe_window import RecipeWindow
from backend_window import BackendWindow
import subprocess
import copy
from run_cyclus import cyclus_run
import cyclus_gui.tools.from_pris as fp
from hovertip import CreateToolTip


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
        self.master = master
        # self.master.geometry('+0+0')
        self.init_window()
        self.guide()

    def init_window(self):
        self.master.title('GUI')

        # menu instance
        menu = Menu(self.master)
        # self.master.config(menu=menu)


        self.hash_var = StringVar()
        self.hash_var.set(uniq_id)

        """ menu functions not in use
        file = Menu(menu)
        file.add_command(label='Exit', command=self.client_exit)
        menu.add_cascade(label='File', menu=file)


        edit = Menu(menu)
        edit.add_command(label='undo')
        edit.add_command(label='copy')
        # this cascade will have all the commands in edit
        menu.add_cascade(label='Edit', menu=edit)
        """

        columnspan=5
        q = Label(root, text='Cyclus Helper', bg='yellow')
        q.grid(row=0, columnspan=columnspan)
        CreateToolTip(q, text='huehuehuehuehue\n huehuehuehuehue')
        Label(root, textvariable=self.hash_var, bg='pale green').grid(row=1, columnspan=columnspan)
        Label(root, text='====================================').grid(row=2, columnspan=columnspan)
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
        CreateToolTip(load_button, text='You can load from a previous instance.\nFor every instance, the GUI automatically creates `output_xxx` directory\nwhere it saves all the files, so that it can be called later on.')
        load_button.grid(row=6, column=2)

        load_complete_input = Button(root, text='From xml', command=lambda: self.load_full_xml())
        CreateToolTip(load_complete_input, text='You can load from a previously-existing Cyclus input xml file.\nThere are limitations to some input files, if they use special archetypes. You can edit or run cyclus on the file!')
        load_complete_input.grid(row=7, column=2)

        load_pris = Button(root, text='From PRIS', command=lambda: self.load_from_pris())
        CreateToolTip(load_pris, text='You can initialize a simulation to a real-world initial condition!\nUsing this method the real-life fleet is automatically generated from the\nIAEA Power Reactor Information System (PRIS) database.')
        load_pris.grid(row=8, column=2)



        make_input_button = Button(root, text='Generate Input', command=lambda: self.check_and_run(run=False))
        CreateToolTip(make_input_button, text='Compile the input (into `input.xml`)\nbut not run the file')
        make_input_button.grid(row=6, column=4)


        combine_run_button = Button(root, text='Combine and Run', command= lambda: self.check_and_run())
        CreateToolTip(combine_run_button, text='You can compile and run this simulation\nYou can do this locally if you have a local installation of Cyclus\nBut you can also run it remotely.')
        combine_run_button.grid(row=7, column=4)

        backend_button = Button(root, text='Backend Analysis', command= lambda: self.open_window('backend', output_path))
        CreateToolTip(backend_button, text='After getting the output file, you can get plots and csv files\nwith ease using this module.')
        backend_button.grid(row=8, column=4)



    def client_exit(self):
        exit()


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

    def load_prev_window(self):
        self.load_window = Toplevel(self.master)
        self.load_window.title('Load previous with hash')
        Label(self.load_window, text='Enter id:', bg='yellow').pack()
        entry = Entry(self.load_window)
        entry.pack()
        Button(self.load_window, text='Load!', command=lambda: self.load_prev(entry)).pack()


    def load_prev(self, entry):
        folders = os.listdir(file_path)
        folders = [f for f in folders if os.path.isdir(os.path.join(file_path, f))]
        hash_ = str(entry.get())
        for i in folders:
            if hash_ in i:
                files_in = os.listdir(os.path.join(file_path, 'output_%s'%hash_))
                info_text = 'Found folder %s.\nLoading input blocks:\n\n' %i
                for f_ in files_in:
                    f_ = f_.replace('.xml', '')
                    info_text += '\t%s\n' %f_
                messagebox.showinfo('Found!', info_text)
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
        

    def load_full_xml(self):
        self.load_xml_window = Toplevel(self.master)
        self.load_xml_window.title('Load full xml file')
        Label(self.load_xml_window, text='Choose a file to load!').pack()
        Button(self.load_xml_window, text='Browse', command= lambda : self.askopenfile()).pack()



    def askopenfile(self):
        file = filedialog.askopenfile(parent=self.load_xml_window, mode='r', title='Choose an xml file')
        self.load_xml_file(file)
        messagebox.showinfo('Successfully loaded file', 'Successfully loaded file')
        self.load_xml_window.destroy()


    def load_xml_file(self, file):
        xml_dict = xmltodict.parse(file.read())['simulation']
        # check if file is good:
        elements = ['control', 'archetypes', 'facility', 'region', 'recipe']
        if list(xml_dict.keys()) != elements:
            messagebox.showerror('Error', 'This is a malformed xml file! Check file to see if it has all the nodes:\nIt needs:\n%s\n\nBut it only has:\n %s' %(', '.join(elements), ', '.join(list(xml_dict.keys()))))

        for part in elements:
            with open(os.path.join(output_path, part+'.xml'), 'w') as f:
                if part in ['facility', 'region', 'recipe']:
                    f.write('<root>')
                f.write(xmltodict.unparse({part: xml_dict[part]}, pretty=True, full_document=False))
                if part in ['facility', 'region', 'recipe']:
                    f.write('</root>')


    def load_from_pris(self):
        guide_text = """
        You can `initialize' your simulation as a real-life nation!
        This method loads from the PRIS database and deploys reactors in your
        desired country, in a desired initial time. The reactor lifetimes
        are calculated as a remaining lifetime.

        Assumptions:
        1. Reactors below 100 MWe are filtered out (assumed to be research reactors)
        2. Core size is linearly scaled with power capacity
        3. Reactor lifetimes are all assumed to be 60 years from their first criticality date
        4. Fuel Cycle facilities are deployed with infinite capacity.

        Simulation defaults:
        1. Reactors are cycamore::Reactor (recipe reactors)
        2. By default deploys a `RandLand' region with `Fuel_Cycle_Facilities' institution with facilities:
           a. `nat_u_source' -> [natl_u]
           b. [natl_u] -> `enrichment' -> [uox]
           c. [uox_waste, used_candu, mox_waste, tailings, reprocess_waste] -> `SomeSink'
           d. [Pu, tailings] -> `mixer' -> mox (9% Pu, 91% tailings)
           e. [uox_waste] -> `reprocessing' -> ['Pu', 'U']
        """
        self.guide(guide_text)


        self.load_from_pris_window = Toplevel(self.master)
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
        self.country_select_window = Toplevel(self.load_from_pris_window)
        self.selected_countries = []
        self.country_select_window.title('Select Countries')
        # get lists of countries
        self.pris_csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'src', 'pris.csv')
        with open(self.pris_csv_path, 'r') as f:
            q = f.readlines()
        country_list = sorted(list(set([w.split(',')[0] for w in q if 'Country' not in w])))
        Label(self.country_select_window, text='Click on country to select:').grid(row=0, column=0)
        self.button_color = {}
        self.button_loc = {}
        for indx, c in enumerate(country_list):
            self.button_color[c] = Button(self.country_select_window, text=c, command=lambda country=c : self.add_country(country), fg='black')
            self.button_color[c].grid(row=indx+1, column=0)
            self.button_loc[c] = indx+1


    def add_country(self, country):
        if country in self.selected_countries:
            self.selected_countries.remove(country)
            self.button_color[country] = Button(self.country_select_window, text=country, command=lambda country=country: self.add_country(country), fg='black').grid(row=self.button_loc[country], column=0)
        else:
            self.selected_countries.append(country)
            self.button_color[country] = Button(self.country_select_window, text=country, command=lambda country=country: self.add_country(country), fg='green', foreground='green').grid(row=self.button_loc[country], column=0)


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
            messagebox.showinfo('Successfully loaded file', 'Successfully loaded file with countries\n\n '+'\n'.join(self.selected_countries))
            self.load_from_pris_window.destroy()


    def check_and_run(self, run=True):
        files = os.listdir(output_path)
        okay = True
        absentee = []
        file_list = ['control.xml', 'archetypes.xml', 'facility.xml',
                     'region.xml', 'recipe.xml']
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
            input_file = '<simulation>\n'
            for i in file_list:
                skipfront = 0
                skipback = 0
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
            input_file += '\n</simulation>'
            with open(os.path.join(output_path, 'input.xml'), 'w') as f:
                f.write(input_file)
            if run:                
                input_path = os.path.join(output_path, 'input.xml')
                output = os.path.join(output_path, 'cyclus.sqlite')
                run = cyclus_run(self.master, input_path, output)


    def guide(self, guide_text=''):
        try: self.guide_window.destroy()
        except: z=0
        self.guide_window = Toplevel(self.master)
        self.guide_window.title('Guide')
        self.guide_window.geometry('+500+0')
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
        Label(self.guide_window, text=guide_text, justify=LEFT).pack(padx=30, pady=30)




root = Tk()
#root.geometry('400x300')
app = Cygui(root)
root.mainloop()




