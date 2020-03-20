from tkinter import *
from tkinter import messagebox
from tkinter import filedialog
from tkinter.scrolledtext import ScrolledText
import xmltodict
import uuid
import os
import http.client
import shutil
import json
import paramiko
import copy
from cyclus_gui.gui.run_cyclus import cyclus_run
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
        self.meta_file_path = os.path.join(self.output_path, 'm.json')
        if os.path.isfile(os.path.join(self.output_path, 'archetypes.xml')): 
            self.arche, self.n = read_xml(os.path.join(self.output_path, 'archetypes.xml'), 'arche')
        else:
            try:
                command = 'cyclus -m'
                process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
                jtxt = process.stdout.read()
                with open(self.meta_file_path, 'wb') as f:
                    f.write(jtxt)
                self.arche = self.read_metafile(self.meta_file_path)
                messagebox.showinfo('Found', 'Found Cyclus, automatically grabbing archetype libraries :)')
            except:
                try:
                    # try to download m.json from gitlab
                    url = 'https://code.ornl.gov/4ib/cyclus_gui/raw/master/src/m.json'
                    urllib.request.urlretrieve(url, self.meta_file_path)
                    self.arche = self.read_metafile(self.meta_file_path)
                    messagebox.showinfo('Downloaded', 'Downloaded metadata from https://code.ornl.gov/4ib/cyclus_gui/\nIt seems like you do not have Cyclus.\n So I filled this for you :)')
                except:
                    messagebox.showinfo('No Internet', 'No internet, so we are going to use metadata saved in the package.\n Using all cyclus/cycamore arcehtypes as default.')
        self.default_arche = copy.deepcopy(self.arche)
        


        Button(self.master, text='Add Row', command= lambda : self.add_more()).grid(row=1)
        Button(self.master, text='Add!', command= lambda : self.add()).grid(row=2)
        Button(self.master, text='Default', command= lambda: self.to_default()).grid(row=3)
        Button(self.master, text='Import libraries (local)', command= lambda: self.import_libraries(local=True)).grid(row=4)
        Button(self.master, text='Import libraries (remote)', command= lambda: self.import_libraries(local=False)).grid(row=5)


        Label(self.master, text='').grid(row=6)

        Button(self.master, text='Done', command= lambda: self.done()).grid(row=7)
        Label(self.master, text='Library').grid(row=0, column=2)
        Label(self.master, text='Archetype').grid(row=0, column=3)
        self.entry_list = []
        self.additional_arche = []
        self.rownum = 1

        # status window
        self.update_loaded_modules_window()


    def import_libraries(self, local):
        self.import_window = Toplevel(self.master)
        if local:
            self.import_window.title('Load metadata from local Cyclus installation')
            Label(self.import_window, text='Cyclus executable path / command:', bg='yellow').pack()
            entry = Entry(self.import_window)
            entry.pack()
            Button(self.import_window, text='Import', command=lambda:self.locally_import(entry)).pack()
        else:
            self.import_window.title('Load metadata from remote Cyclus installation')
            Label(self.import_window, text='Server / IP:').grid(row=0, column=0)
            server = Entry(self.import_window)
            server.insert(END, 'azure')
            server.grid(row=0, column=1)

            Label(self.import_window, text='Username:').grid(row=1, column=0)
            username = Entry(self.import_window)
            username.grid(row=1, column=1)

            Label(self.import_window, text='Password:').grid(row=2, column=0)
            password = Entry(self.import_window)
            password.grid(row=2, column=1)

            Label(self.import_window, text='Proxy Hostname:').grid(row=3, column=0)
            proxy = Entry(self.import_window)
            proxy.grid(row=3, column=1)

            Label(self.import_window, text='Proxy Port:').grid(row=4, column=0)
            proxy_port = Entry(self.import_window)
            proxy_port.grid(row=4, column=1)

            Button(self.import_window, text='Import', command=lambda:self.remote_import(server, username, password, proxy, proxy_port)).grid(row=5, columnspan=2)

    def remote_import(self, server, username, password, proxy, proxy_port):
        if server.get() == 'azure':
            ip = '40.121.41.236'
        else:
            ip = server.get()

        username = username.get()
        password = password.get()
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        proxy_hostname = proxy.get()
        proxy_port = proxy_port.get()
        try:
            if proxy_hostname != '':
                http_con = http.client.HTTPConnection(proxy_hostname, proxy_port)
                headers = {}
                http_con.set_tunnel(ip, 22, headers)
                http_con.connect()
                sock = http_con.sock
                ssh.connect(ip, username=username, password=password, sock=sock, allow_agent=False, look_for_keys=False)
            else:
                ssh.connect(ip, username=username, password=password, allow_agent=False, look_for_keys=False)

        except Exception as e:
            messagebox.showerror('Error', 'Connection to remote server failed!\n\n %s' %e)
            self.import_window.destroy()
            return

        i, o, e = ssh.exec_command('/home/baej/.local/bin/cyclus -m')
        output = '\n'.join(o.readlines())
        error = '\n'.join(e.readlines())
        print('output', output)
        print('error', error)
        if len(output) == 0:
            messagebox.showerror('Error', 'Connected, but execution of command \n cyclus -m \n in remote server failed!\n\n %s' %error)
            self.import_window.destroy()
        else:
            print('eh')
            with open(self.meta_file_path, 'w') as f:
                f.write(output)
            messagebox.showinfo('Done', 'Successfully read metadata file!')
            self.arche = self.read_metafile(self.meta_file_path)
            print('e')
            self.update_loaded_modules_window()
            self.import_window.destroy()



    def locally_import(self, entry):
        temp_metafile = self.meta_file_path + '_temp'
        cmd = str(entry.get())
        command = '%s -m > %s' %(cmd, temp_metafile)
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
        out, err = proc.communicate()
        print('out', out)
        print('err', err)
        try:
            self.arche = self.read_metafile(temp_metafile)
            messagebox.showinfo('Success', 'Import successful.')
            shutil.move(temp_metafile, self.meta_file_path)
            self.update_loaded_modules_window()
            self.import_window.destroy()
        except Exception as e:
            for i in [out,err]:
                if i is not None:
                    messagebox.showerror('Error', 'Import failed!\n\n %s' %(i.decode('utf-8')))
            self.import_window.destroy()



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

