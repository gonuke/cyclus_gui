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
import urllib.request
import subprocess
from cyclus_gui.gui.read_xml import *


class ArchetypeWindow(Frame):
    def __init__(self, master, output_path):
        """
        arche looks like:
        array = []
        [0] = library
        [1] = archetype name
        """

        self.screen_width = master.winfo_screenwidth()
        self.screen_height = master.winfo_screenheight()
        self.master = Toplevel(master)
        self.output_path = output_path
        self.master.geometry('+0+%s' %(int(self.screen_height//3)))
        self.guide()
        self.arche = [['agents', 'NullInst'], ['agents', 'NullRegion'], ['cycamore', 'Source'],
                      ['cycamore', 'Sink'], ['cycamore', 'DeployInst'], ['cycamore', 'Enrichment'],
                      ['cycamore', 'FuelFab'], ['cycamore', 'GrowthRegion'], ['cycamore', 'ManagerInst'],
                      ['cycamore', 'Mixer'], ['cycamore', 'Reactor'], ['cycamore', 'Separations'],
                      ['cycamore', 'Storage']]
        meta_file_path = os.path.join(self.output_path, 'm.json')
        if os.path.isfile(os.path.join(self.output_path, 'archetypes.xml')): 
            self.arche, self.n = read_xml(os.path.join(self.output_path, 'archetypes.xml'), 'arche')
        else:
            try:
                command = 'cyclus -m'
                process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
                jtxt = process.stdout.read()
                with open(meta_file_path, 'wb') as f:
                    f.write(jtxt)
                self.arche = self.read_metafile(meta_file_path)
                messagebox.showinfo('Found', 'Found Cyclus, automatically grabbing archetype libraries :)')
            except:
                try:
                    # try to download m.json from gitlab
                    url = 'https://code.ornl.gov/4ib/cyclus_gui/raw/master/src/m.json'
                    urllib.request.urlretrieve(url, meta_file_path)
                    self.arche = self.read_metafile(meta_file_path)
                    messagebox.showinfo('Downloaded', 'Downloaded metadata from https://code.ornl.gov/4ib/cyclus_gui/\nIt seems like you do not have Cyclus.\n So I filled this for you :)')
                except:
                    messagebox.showinfo('No Internet', 'No internet, so we are going to use metadata saved in the package.\n Using all cyclus/cycamore arcehtypes as default.')
        self.default_arche = copy.deepcopy(self.arche)
        


        Button(self.master, text='Add Row', command= lambda : self.add_more()).grid(row=1)
        Button(self.master, text='Add!', command= lambda : self.add()).grid(row=2)
        Button(self.master, text='Default', command= lambda: self.to_default()).grid(row=3)

        Label(self.master, text='').grid(row=4)

        Button(self.master, text='Done', command= lambda: self.done()).grid(row=5)
        Label(self.master, text='Library').grid(row=0, column=2)
        Label(self.master, text='Archetype').grid(row=0, column=3)
        self.entry_list = []
        self.additional_arche = []
        self.rownum = 1

        # status window
        self.update_loaded_modules_window()

    def read_metafile(self, meta_file_path):
        with open(meta_file_path, 'r') as f:
            jtxt = f.read()
        j = json.loads(jtxt)
        arche = j['specs']
        arche = [[q[0], q[1]] for q in (i[1:].split(':') for i in arche)]
        return arche


    def update_loaded_modules_window(self):
        """ this functions updates the label object in the status window
            so the loaded archetypes are updated live"""
        try:
            self.status_window.destroy()
        except:
            z=0

        self.status_window = Toplevel(self.master)
        self.status_window.geometry('+%s+0' %int(self.screen_width/3))
        Label(self.status_window, text='Loaded modules:', bg='yellow').grid(row=0, columnspan=2)
        row = 1
        for i in self.arche:
            Label(self.status_window, text=i[0] + '::' + i[1]).grid(row=row, column=0)
            # lib_name = [copy.deepcopy(i[0]), copy.deepcopy(i[1])]
            Button(self.status_window, text='x', command=lambda i=i: self.delete_arche([i[0], i[1]])).grid(row=row, column=1)
            row += 1


    def delete_arche(self, lib_name):
        for indx, val in enumerate(self.arche):
            if val == lib_name:
                it = indx
        del self.arche[it]
        self.update_loaded_modules_window()


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
        self.update_loaded_modules_window()

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
            self.update_loaded_modules_window()


    def done(self):
        string = '<archetypes>\n'
        for pair in self.arche:
            string += '\t<spec>\t<lib>%s</lib>\t<name>%s</name></spec>\n' %(pair[0], pair[1])
        string += '</archetypes>\n'
        with open(os.path.join(self.output_path, 'archetypes.xml'), 'w') as f:
            f.write(string)
        self.master.destroy()

    def guide(self):

        self.guide_window = Toplevel(self.master)
        self.guide_window.geometry('+%s+0' %int(self.screen_width/1.2))
        guide_string = """
        All Cyclus and Cycamore archetypes are already added. If there are additional archetypes
        you would like to add, click the `Add Row' button, type in the library and archetype,
        and press `Add!'.

        Try not to delete cycamore::DeployInst and agents::NullRegion, since they are the
        default for this GUI.

        If you made a mistake, you can go back to the default Cyclus + Cycamore
        archetypes by clicking `Default'.

        Once you're done, click `Done'.


        FOR MORE INFORMATION:
        http://fuelcycle.org/user/input_specs/archetypes.html
        """
        Label(self.guide_window, text=guide_string, justify=LEFT).pack(padx=30, pady=30)

