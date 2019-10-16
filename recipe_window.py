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


class RecipeWindow(Frame):
    """ Note: Recipes are generated with <root> parent node for xml for parsing reasons

        recipe_dict:
        key: recipe name
        val: dict
             key: 'base', 'composition'
             val: str(base), dict(composition)
                             key: isotope name
                             val: frac (base-frac)
    """

    def __init__(self, master, output_path):
        self.master = Toplevel(master)
        self.master.title('Define recipes')
        self.output_path = output_path
        self.master.geometry('+0+900')
        self.guide()
        browse_button = Button(self.master, text='Add From File [atomic]', command=lambda : self.askopenfile('atom')).grid(row=1)
        browse_button = Button(self.master, text='Add From File [mass]', command= lambda : self.askopenfile('mass')).grid(row=2)
        Button(self.master, text='Add all from Directory [atomic]', command=lambda : self.askopendir('atom')).grid(row=3)
        Button(self.master, text='Add all from Directory [mass]', command=lambda : self.askopendir('mass')).grid(row=4)
        Button(self.master, text='Add Recipe Manually [atomic]', command=lambda : self.add_recipe('atom')).grid(row=5)
        Button(self.master, text='Add Recipe Manually [mass]', command=lambda : self.add_recipe('mass')).grid(row=6)

        Label(self.master, text='').grid(row=7)

        Button(self.master, text='Finish', command=lambda: self.done()).grid(row=8)
        self.recipe_dict = {}

        if os.path.isfile(os.path.join(self.output_path, 'recipes.xml')):
            self.read_xml()

        self.update_loaded_recipes()


    def update_loaded_recipes(self):
        try:
            self.status_window.destroy()
        except:
            z=0

        self.status_window = Toplevel(self.master)
        self.status_window.title('Defined Recipes')
        self.status_window.geometry('+250+900')
        Label(self.status_window, text='Loaded recipes:').grid(row=0, columnspan=2)
        row=1
        for key in self.recipe_dict:
            Button(self.status_window, text='x', command=lambda key=key: self.del_recipe(key)).grid(row=row, column=0)
            Button(self.status_window, text=key, command=lambda key=key: self.edit_recipe(key)).grid(row=row, column=1)
            row += 1


    def del_recipe(self, recipename):
        self.recipe_dict.pop(recipename, None)
        self.update_loaded_recipes()

    def edit_recipe(self, recipename):
        self.add_recipe(self.recipe_dict[recipename]['base'])
        self.name_entry.insert(END, recipename)
        string = ''
        for iso, val in self.recipe_dict[recipename]['composition'].items():
            string += '%s\t%s\n' %(iso,val)
        self.textfield.insert(INSERT, string)


    def add_recipe(self, atom_or_mass):
        """
        Button add recipe will prompt user-input recipe name and text
        """
        self.addrecipe_window = Toplevel(self.master)
        self.addrecipe_window.title('New recipe definition (%s)' %atom_or_mass)
        self.addrecipe_window.geometry('+800+400')

        Button(self.addrecipe_window, text='Done!',
               command= lambda : self.send_input(self.name_entry, self.textfield, self.addrecipe_window, atom_or_mass)).grid(row=0, columnspan=2)
        Label(self.addrecipe_window, text='Recipe name').grid(row=1, column=0)
        self.name_entry = Entry(self.addrecipe_window)
        self.name_entry.grid(row=1, column=1)
        Label(self.addrecipe_window, text='Recipe:').grid(row=2, columnspan=2)
        self.textfield = ScrolledText(self.addrecipe_window, wrap=WORD)
        self.textfield.grid(row=3, columnspan=2)


    def send_input(self, name, text, window, atom_or_mass):
        """
        Gets the entry and scrolltext objects and obtains the actual data
        and sends it to recipe_input for testing and storage.
        """
        name = name.get() + '_' + atom_or_mass
        text = str(text.get(1.0, END))
        self.recipe_input(name, text, window)

    def read_xml(self):
        with open(os.path.join(self.output_path, 'recipes.xml'), 'r') as f:
            xml_list = xmltodict.parse(f.read())['root']['recipe']
            if 'dict' in str(type(xml_list)).lower():
                # if there's only one recipe entry, it will return
                # a dictionary instead of a list
                xml_list = [xml_list]
            for recipe in xml_list:
                comp_dict = {}
                # if there's only one nuclide, it will return
                # a dictionary instead of a list
                if 'dict' in str(type(recipe['nuclide'])).lower():
                    recipe['nuclide'] = [recipe['nuclide']]
                for entry in recipe['nuclide']:
                    comp_dict[entry['id']] = entry['comp']
                self.recipe_dict[recipe['name']] = {'base': recipe['basis'],
                                                    'composition': comp_dict}


    def recipe_input(self, name, text, window):
        if name == '' or text == '':
            messagebox.showerror('Name or text missing! :(')
            return
        if name.split('_')[-1] not in ['atom', 'mass']:
            raise ValueError('Something Wrong man, either has to have _atom or _mass appended')
        base = name.split('_')[-1]
        name = name.replace('_'+base, '')


        # check input
        # if it recognizes a comma, then we are going to
        # look at it as a csv file
        # if not, its just the plaintext format
        if ',' in text:
            text = text.replace(',', ' ')    
        composition_dict = self.parse_plaintext(text)
        print(composition_dict)


        if composition_dict == None:
            messagebox.showerror('Error', 'The recipe text (%s) is malformed! :( ' %name)
            return


        self.recipe_dict[name] = {'base': base,
                                  'composition': composition_dict}
        print(self.recipe_dict)
        # if not good, error message
        # if good, kill window
        messagebox.showinfo('Recipe Saved', 'Recipe %s is saved!' %name)
        if window != None:
            window.destroy()
        self.update_loaded_recipes()


    def parse_plaintext(self, text):
        composition_dict = {}
        for row in text.split('\n'):
            if row == '':
                continue
            e = row.split()
            composition_dict[e[0]] = float(e[1])        
        return composition_dict


    def askopenfile(self, base):
        file = filedialog.askopenfile(parent=self.master, mode='r', title='Choose a file')
        filename = os.path.splitext(os.path.basename(file.name))[0] + '_' + base
        data = file.read()
        
        self.recipe_input(filename, data, None)

    def askopendir(self, base):
        file = filedialog.askdirectory()
        files = os.listdir(file)
        print(files)
        for filename in files:
            f = open(os.path.join(file, filename), 'r')
            data = f.read()
            filename = filename.split('.')[0]
            filename_base = filename+'_'+base
            self.recipe_input(filename_base, data, None)



    def done(self):
        string = '<root>\n'
        if len(self.recipe_dict.keys()) == 0:
            messagebox.showerror('Error', 'There are no recipes to output :(')
            return
        temp = '<recipe>\n\t<name>{name}</name>\n\t<basis>{base}</basis>\n{recipe}</recipe>\n'
        
        for key in self.recipe_dict:
            comp_string = ''
            for iso, comp in self.recipe_dict[key]['composition'].items():
                comp_string += '\t<nuclide>\t<id>%s</id>\t<comp>%f</comp>\t</nuclide>\n' %(iso, comp)
            name = key
            base = self.recipe_dict[key]['base']
            string += temp.format(name=name,
                                  base=base,
                                  recipe=comp_string)
            string += '\n'
        string += '</root>'
        with open(os.path.join(self.output_path, 'recipes.xml'), 'w') as f:
            f.write(string)
        messagebox.showinfo('Success', 'Successfully rendered %i recipes! :)' %len(self.recipe_dict.keys()))
        self.master.destroy()

    def guide(self):
        self.guide_window = Toplevel(self.master)
        self.guide_window.title('Recipe guide')
        self.guide_window.geometry('+0+400')
        guide_string = """
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

        When you add recipe from a file, the filename becomes the recipe name.
        You can also add multiple recipes at a time by selecting a directory
        that contains multiple recipe files.
        """
        Label(self.guide_window, text=guide_string, justify=LEFT).pack(padx=30, pady=30)

