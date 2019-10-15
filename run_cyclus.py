from tkinter import *
from PIL import Image, ImageTk
from tkinter import messagebox
from tkinter import filedialog
from tkinter.scrolledtext import ScrolledText
import xml.etree.ElementTree as et
import xmltodict
import http.client
import uuid
import os
import seaborn as sns
import shutil
import json
import copy
import paramiko
import uuid
import subprocess
import time
import os

class cyclus_run:
    def __init__(self, master, input_path, output_path):

        self.input_path = input_path
        self.output_path = output_path

        # open new window
        self.master = Toplevel(master)
        self.master.title('Running Cyclus')
        self.master.geometry('+1000+700')
        # configure page
        columnspan = 5
        Label(self.master, text='Cyclus Run configuration').grid(row=0, columnspan=columnspan)
        Label(self.master, text='========================').grid(row=1, columnspan=columnspan)
        
        local_run = Button(self.master, text='Run Locally', command=lambda:self.run_locally())
        local_run.grid(row=2, column=0)
        Label(self.master, text='Cyclus command/path:').grid(row=2, column=1)
        self.cyclus_cmd = Entry(self.master)
        self.cyclus_cmd.insert(END, 'cyclus')
        self.cyclus_cmd.grid(row=2, column=2)
        
        cloud_run = Button(self.master, text='Run on Cloud', command=lambda:self.run_on_cloud())
        cloud_run.grid(row=3, column=0)
        Label(self.master, text='Proxy Hostname:').grid(row=3, column=1)
        self.proxy_hostname = Entry(self.master)
        self.proxy_hostname.grid(row=3, column=2)
        Label(self.master, text='Proxy Port:').grid(row=3, column=3)
        self.proxy_port = Entry(self.master)
        self.proxy_port.grid(row=3, column=4)
        
        
        frame = Frame(self.master)
        frame.grid(row=4, columnspan=columnspan)

        s = Scrollbar(frame)
        s.pack(side=RIGHT, fill=Y)
        self.output_pipe = Text(frame, wrap='word')
        s.config(command=self.output_pipe.yview)
        self.output_pipe.pack(side=LEFT, fill=Y)
        self.output_pipe.config(yscrollcommand=s.set)
        self.output_pipe.insert(END, 'This is where the outputs of Cyclus run will be displayed\n\n')


    def run_locally(self):
        # check if output exists, and if it does, change its name to temp_whatever
        self.output_pipe.insert(END, '\nChecking if output `cyclus.sqlite` already exists...')
        if os.path.isfile(self.output_path):
            i = 1
            self.outdir = os.path.dirnmae(self.output_path)
            while os.path.isfile(os.path.join(self.outdir, 'temp_%s.sqlite' %str(i))):
                i += 1
            self.output_pipe.insert(END, '\n`cyclus.sqlite` already exists! Changing the previous filename to temp_%s.sqlite\n' %str(i))
            os.rename(os.path.join(self.outdir, 'temp_%s.sqlite' %str(i)))

        # run cyclus 
        self.output_pipe.insert(END, '\nAttempting to run Cyclus locally:')
        cyclus_cmd = self.cyclus_cmd.get()
        command = '%s %s -o %s' %(cyclus_cmd, self.input_path, self.output_path)
        self.output_pipe.insert(END, '\nRunning command:')
        self.output_pipe.insert(END, '\n'+command)
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
        out, err = proc.communicate()
        print(out)
        print(err)
        self.output_pipe.insert(END, '\n\n'+out.decode('utf-8'))
        if 'success' in out.decode('utf-8'):
            self.output_pipe.insert(END, '\n\nGreat! move on to the backend analysis!')



    def run_on_cloud(self):
        # microsoft azure account
        ip = '40.121.41.236'
        self.username = 'user1'
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.output_pipe.insert(END, '\nAttempting to connect to Azure VM:')
        proxy_hostname = self.proxy_hostname.get()
        proxy_port = self.proxy_port.get()
        try:
            if proxy_hostname != '':
                self.output_pipe.insert(END, '\n' + 'with Proxy hostname=%s and port=%s' %(proxy_hostname, proxy_port))
                http_con  = http.client.HTTPConnection(proxy_hostname, proxy_port)
                # this should be changed?
                headers = {}

                http_con.set_tunnel(ip, 22, headers)
                http_con.connect()
                sock = http_con.sock
                self.ssh.connect(ip, username=self.username,
                                 password=' ', sock=sock)

            else:
                self.ssh.connect(ip, username=self.username,
                                 password=' ')
            self.output_pipe.insert(END, '\n\n CONNECTED. Now uploading generated input file, running the file on the VM, and downloading the file:\n\n')
            self.upload_run_download(self.input_path, self.output_path)
            self.return_code = 0

        except Exception as e:
            self.err_message = """Did not connect! Check Internet connection or contact baej@ornl.gov
If you are using this in a secure network, that might be the reason as well.
Try using a tunneling application (ex. Corkscrew) to use a proxy, by defining the `ProxyCommand' block.
https://wiki.archlinux.org/index.php/HTTP_tunneling


Error message:\n""" + str(e)
            self.output_pipe.insert(END, '\n\n' + self.err_message)
            self.return_code = -1



    def run_and_print(self, command, p=False):
        if p:
            self.output_pipe.insert(END, 'Running command:\n%s\n' %command)
            self.output_pipe.insert(END, '============================\n')
        i, o, e = self.ssh.exec_command(command)
        output = '\n'.join(o.readlines())
        error = '\n'.join(e.readlines())
        if len(error) != 0:
            if p:
                self.output_pipe.insert(END, 'Error:\n')
                self.output_pipe.insert(END, error)
                self.output_pipe.insert(END, '\n\n')
            return error
        if p:
            self.output_pipe.insert(END, 'Output:\n')
            self.output_pipe.insert(END,output)
            self.output_pipe.insert(END, '\n')
            self.output_pipe.insert(END, '============================\n')
            self.output_pipe.insert(END, 'Finish\n')
        return 0

    def upload_run_download(self, input_path, output_path):
        ftp = self.ssh.open_sftp()
        # upload yo

        rnd_dir = '/home/%s/%s' %(self.username, str(uuid.uuid4()))
        remote_input_path = os.path.join(rnd_dir, 'input.xml')

        # make temporary directory with random hash so no overlap
        # during simultaneous run
        if self.run_and_print('mkdir %s' %rnd_dir) != 0:
            raise ValueError('That hash file already exists..')
        # upload generated input file
        self.output_pipe.insert(END, '\n Uploading input file to %s' %remote_input_path)
        ftp.put(input_path, remote_input_path)
        
        # run Cyclus
        remote_output_path = remote_input_path.replace('input.xml',
                                                       'cyclus.sqlite')
        c = self.run_and_print('/home/baej/.local/bin/cyclus %s -o %s --warn-limit 0' %(remote_input_path,
                                                                         remote_output_path), p=True)
        if c == 0 or ('error' not in c and 'Abort' not in c and 'fatal' not in c):
            # download yo
            self.output_pipe.insert(END, '\n Run Successful. Now downloading output back into local drive:\n')
            ftp.get(remote_output_path, output_path)
            time.sleep(5)
            self.output_pipe.insert(END, '\n All done! Now proceed to backend analysis for some plots and data\n')
            # delete file
            #self.run_and_print('rm -rf %s' %rnd_dir)

        else:
            self.err_message = 'Cyclus run failed! Check terminal output'
            self.output_pipe.insert(END, '\n\n')
            self.output_pipe.insert(END, self.err_message)
            self.return_code = -2


