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


class SimulationWindow():
    """ This is the simulation window where it takes input from the user on
        simulation parameters and makes a Cyclus control box
        
        entry_dict looks like:
        key: criteria
        val: value
    """
    def __init__(self, master, output_path):
        self.master = Toplevel(master)
        self.master.title('Simulation definition')
        self.output_path = output_path
        # self.frame = Frame(self.master)
        self.master.geometry('+0+500')
        self.guide()
        inputs = ['duration', 'startmonth', 'startyear', 'decay',
                  'explicit_inventory', 'dt']
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

        if os.path.isfile(os.path.join(self.output_path, 'simulation.xml')):
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
        with open(os.path.join(self.output_path, 'simulation.xml'), 'r') as f:
            xml_dict = xmltodict.parse(f.read())['control']
        for key, val in xml_dict.items():
            self.entry_dict[key].delete(0, END)
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
            messagebox.showeror('Error', 'Month has to be number from 1 to 12')
        elif self.entry_dict['decay'] not in ['never', 'lazy', 'manual']:
            messagebox.showerror('Error', 'Decay must be either never, lazy, or manual')
        elif not self.is_it_pos_integer(self.entry_dict['dt']):
            messagebox.showerror('Error', 'dt must be a positive integer')
        else:
            messagebox.showinfo('Success', 'Rendered Simulation definition into xml! :)')
            xml_string = '<control>\n'
            for key, val in self.entry_dict.items():
                if key=='dt' and int(val)==2629846:
                    continue
                if (key=='explicit_inventory' or key=='explicit_inventory_compact') and int(val)==0:
                    continue
                xml_string+='\t<%s>%s</%s>\n' %(key, val, key)
            xml_string += '</control>\n'
            with open(os.path.join(self.output_path, 'simulation.xml'), 'w') as f:
                f.write(xml_string)

            self.master.destroy()

    def guide(self):

        self.guide_window = Toplevel(self.master)
        self.guide_window.title('Simulation guide')
        self.guide_window.geometry('+0+3500')

        guide_string = """
        duration = Duration of the simulation

        startmonth = Starting month of the simulation [1-12]
        
        startyear = Starting year of the simulation
        
        decay = Decay solver [never, lazy, manual]
        
        explicit_inventory =  Create ExplicitInventory table [0,1]
        If you want to get the inventory of each facility at each timestep,
        write 1
             
        dt = Duration of single timestep in seconds (default is a month -> 2,629,846)

        FOR MORE INFORMATION:
        http://fuelcycle.org/user/input_specs/control.html
        """
        Label(self.guide_window, text=guide_string, justify=LEFT).pack(padx=30, pady=30)

