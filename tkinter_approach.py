from tkinter import *
from PIL import Image, ImageTk
from tkinter import messagebox
from tkinter import filedialog
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
        self.newWindow = Toplevel(self.master)

        if name == 'simulation':
            self.app = SimulationWindow(self.newWindow)
        if name == 'archetype':
            self.app = ArchetypeWindow(self.newWindow)
        if name == 'prototype':
            self.app = PrototypeWindow(self.newWindow)
        if name == 'region':
            self.app = RegionWindow(self.newWindow)
        if name == 'recipe':
            self.app = RecipeWindow(self.newWindow)

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
                  'region.xml', 'recipe.xml']:
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



class SimulationWindow(Frame):
    """ This is the simulation window where it takes input from the user on
        simulation parameters and makes a Cyclus control box
    """
    def __init__(self, master):
        self.master = master
        self.frame = Frame(self.master)
        master.geometry('800x600')
        inputs = ['duration', 'startmonth', 'startyear', 'decay',
                  'explicit_inventory', 'explicit_inventory_compact',
                  'dt']
        dscr = ['Duration of the simulation in dt (default is months)',
                'Starting month of the simulation[1-12]',
                'Starting year of the simulation',
                'Decay solver - [never, lazy, manual]',
                'create ExplicitInventory table [0, 1]',
                'create ExplicitInventoryCompact table [0, 1]',
                'Duration of single timestep in seconds']
        for i, txt in enumerate(inputs):
            Label(master, text=dscr[i]).grid(row=2*i)
            Label(master, text=txt).grid(row=(2*i +1))

        self.entry_dict = {}
        for row, txt in enumerate(inputs):
            self.entry_dict[txt] = Entry(master)
            self.entry_dict[txt].grid(row=row*2+1, column=1)

        # default values
        self.entry_dict['startyear'].insert(END, 2019)
        self.entry_dict['decay'].insert(END, 'lazy')
        self.entry_dict['dt'].insert(END, 2629846)
        self.entry_dict['explicit_inventory'].insert(END, 0)
        self.entry_dict['explicit_inventory_compact'].insert(END, 0)

        if os.path.isfile(os.path.join(output_path, 'simulation.xml')):
            self.read_xml()

        done_button = Button(self.master, text='Done', command=lambda: self.done())
        done_button.grid(row=len(inputs)*2+1, column=1)
        Label(master, text='For more info:\nhttp://fuelcycle.org/user/input_specs/control.html').grid(row=len(inputs)*2+2, column=0)

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



class ArchetypeWindow(Frame):
    def __init__(self, master):
        self.master = master
        self.frame = Frame(self.master)
        
        self.arche = [['agents', 'NullInst'], ['agents', 'NullRegion'], ['cycamore', 'Source'],
                      ['cycamore', 'Sink'], ['cycamore', 'DeployInst'], ['cycamore', 'Enrichment'],
                      ['cycamore', 'FuelFab'], ['cycamore', 'GrowthRegion'], ['cycamore', 'ManagerInst'],
                      ['cycamore', 'Mixer'], ['cycamore', 'Reactor'], ['cycamore', 'Separations'],
                      ['cycamore', 'Storage']]
        self.default_arche = copy.deepcopy(self.arche)
        if os.path.isfile(os.path.join(output_path, 'archetypes.xml')):
            self.read_xml()



        Label(master, text='All Cyclus and Cycamore agents are already added. If there are additional archetypes you would like to add, list them here:').grid(row=0)
        Button(master, text='Add Row', command= lambda : self.add_more()).grid(row=1)
        Button(master, text='Add!', command= lambda : self.add()).grid(row=2)
        Button(master, text='Default', command= lambda: self.to_default()).grid(row=3)
        Button(master, text='Done', command= lambda: self.done()).grid(row=4)
        Label(master, text='Library').grid(row=0, column=2)
        Label(master, text='Archetype').grid(row=0, column=3)
        self.entry_list = []
        self.additional_arche = []
        self.rownum = 1

        # status window
        self.status_window = Toplevel(master)
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
        self.entry_list = [[x[0].get(), x[1].get()] for x in self.entry_list]
        dont_add_indx = []
        messed_up_indx = []
        err = False
        for indx,entry in enumerate(self.entry_list):
            if entry[0] == '' and entry[1] == '':
                dont_add_indx.append(indx)
            if entry[0] == '' and entry[1] != '':
                messed_up_indx.append(indx)
                err = True
        if err:
            message = 'You messed up on rows:\n'
            for indx in messed_up_indx:
                message += indx + '\t'
            messagebox.showerror('Error', message)
        else:

            string = 'Adding %i new libraries' %(len(self.entry_list) - len(dont_add_indx))
            if len(dont_add_indx) != 0:
                string += '\n Ignoring empty rows: '
                for r in dont_add_indx:
                    string += r + '  '
            for indx, val in enumerate(self.entry_list):
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



class PrototypeWindow(Frame):
    def __init__(self, master):
        self.master = master
        self.frame = Frame(self.master)

    def close_window(self):
        self.master.destroy()



class RegionWindow(Frame):
    def __init__(self, master):
        self.master = master
        self.frame = Frame(self.master)

    def close_window(self):
        self.master.destroy()



class RecipeWindow(Frame):
    def __init__(self, master):
        self.master = master
        self.frame = Frame(self.master)
        browse_button = Button(self.master, text='Browse', command=self.askopenfile)
        browse_button.pack()


    def askopenfile(self):
        file = filedialog.askopenfile(parent=self.master, mode='r', title='Choose a file')
        data = file.read()
        print(data)

    def close_window(self):
        self.master.destroy()



root = Tk()
root.geometry('400x300')
app = Cygui(root)
root.mainloop()
# delete this later
# shutil.rmtree(output_path)




