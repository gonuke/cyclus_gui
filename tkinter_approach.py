from tkinter import *
from PIL import Image, ImageTk
from tkinter import messagebox
from tkinter import filedialog
import xml.etree.ElementTree as et
import xmltodict
import uuid
import os
import shutil

uniq_id = str(uuid.uuid4())
file_path = os.path.abspath(os.path.dirname(__file__))
output_path = os.path.join(file_path, 'output_'+uniq_id)
os.mkdir(output_path)
print('This your hash boy:', uniq_id)

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

        file = Menu(menu)
        file.add_command(label='Exit', command=self.client_exit)
        menu.add_cascade(label='File', menu=file)

        edit = Menu(menu)
        edit.add_command(label='undo')
        edit.add_command(label='copy')
        # this cascade will have all the commands in edit
        menu.add_cascade(label='Edit', menu=edit)



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

    def check_and_run(self):
        files = os.listdir(output_path)
        okay = True
        for i in ['simulation.xml', 'archetype.xml', 'prototype.xml',
                  'region.xml', 'recipe.xml']:
            if i not in files:
                messagebox.showerror('Error', 'You have not made the %s block yet! :(' %i.replace('.xml', ''))
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

        print(self.entry_dict)
        print(self.entry_dict.values())
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

    def close_window(self):
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




