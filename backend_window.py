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
# import analysis as an
import sqlite3 as lite
import numpy as np
import matplotlib.pyplot as plt

class BackendWindow(Frame):
    def __init__(self, master, output_path):
        """
        does backend analysis
        """

        self.master = Toplevel(master)
        self.master.title('Backend Analysis')
        self.output_path = output_path
        self.master.geometry('+0+700')
        self.get_cursor()
        self.get_id_proto_dict()
        self.get_start_times()

        self.guide()
        Label(self.master, text='Choose backend analysis type:').pack()

        raw_table_button = Button(self.master, text='View Raw Tables', command=lambda : self.view_raw_tables())
        raw_table_button.pack()

        material_flow_button = Button(self.master, text='Get Material Flow', command=lambda : self.view_material_flow())
        material_flow_button.pack()

        commodity_transfer_button = Button(self.master, text='Get Commodity Flow', command=lambda : self.commodity_transfer_window())
        commodity_transfer_button.pack()

        deployment_of_agents_button = Button(self.master, text='Get Agent Deployment', command=lambda : self.agent_deployment_window())
        deployment_of_agents_button.pack()

        timeseries_button = Button(self.master, text='Get Timeseries', command=lambda : self.timeseries_window())
        timeseries_button.pack()


    def get_start_times(self):
        i = self.cur.execute('SELECT * FROM info').fetchone()
        self.init_year = i['InitialYear']
        self.init_month = i['InitialMonth']
        self.duration = i['Duration']
        # I guess no dt 
        # self.


    def get_id_proto_dict(self):
        agentids = self.cur.execute('SELECT agentid, prototype, kind FROM agententry').fetchall()
        self.id_proto_dict = {}
        for agent in agentids:
            if agent['kind'] == 'Facility':
                self.id_proto_dict[agent['agentid']] = agent['prototype']


    def get_cursor(self):
        con = lite.connect(os.path.join(self.output_path, 'cyclus.sqlite'))
        con.row_factory = lite.Row
        self.cur = con.cursor()


    def view_raw_tables(self):
        self.raw_table_window = Toplevel(self.master)
        self.raw_table_window.title('View Raw Tables')
        self.raw_table_window.geometry('+0+3500')
        # just like a sql query with ability to export and stuff
        self.guide_text = ''


    def view_material_flow(self):
        self.guide_text = ''
        # show material trade between prototypes
        self.material_flow_window = Toplevel(self.master)
        self.material_flow_window.title('List of transactions to view')
        self.material_flow_window.geometry('+700+1000')
        parent = self.material_flow_window

        traders = self.cur.execute('SELECT DISTINCT senderid, receiverid, commodity FROM transactions').fetchall()
        table_dict = {'sender': [],
                      'receiver': [],
                      'commodity': []}
        if len(traders) > 100:
            messagebox.showinfo('Too much', 'You have %s distinct transaction sets.. Too much for me to show here' %str(len(traders)))
            self.material_flow_window.destroy()
            return
        if len(traders) > 30:
            canvas = Canvas(self.material_flow_window, width=800, height=1000)
            frame = Frame(canvas)
            scrollbar = Scrollbar(self.material_flow_window, command=canvas.yview)
            scrollbar.pack(side=RIGHT, fill='y')
            canvas.pack(side=LEFT, fill='both', expand=True)        
            def on_configure(event):
                canvas.configure(scrollregion=canvas.bbox('all'))
            canvas.configure(yscrollcommand=scrollbar.set)
            frame.bind('<Configure>', on_configure)
            canvas.create_window((4,4), window=frame, anchor='nw')
            parent = frame 

        # create table of sender - receiverid - commodity set like:
        for i in traders:
            table_dict['sender'].append(self.id_proto_dict[i['senderid']] + '(%s)' %str(i['senderid']))
            table_dict['receiver'].append(self.id_proto_dict[i['receiverid']] + '(%s)' %str(i['receiverid']))
            table_dict['commodity'].append(i['commodity'])

        columnspan = 7
        Label(parent, text='List of transactions:').grid(row=0, columnspan=columnspan)
        Label(parent, text='Sender (id)').grid(row=1, column=0)
        Label(parent, text='').grid(row=1, column=1)
        Label(parent, text='Commodity').grid(row=1, column=2)
        Label(parent, text='').grid(row=1, column=3)
        Label(parent, text='Receiver (id)').grid(row=1, column=4)
        Label(parent, text=' ').grid(row=1, column=5)
        Label(parent, text='======================').grid(row=2, columnspan=columnspan)
             
        row = 3
        for indx, val in enumerate(table_dict['sender']):
            Label(parent, text=val).grid(row=row, column=0)
            Label(parent, text='->').grid(row=row, column=1)
            Label(parent, text=table_dict['commodity'][indx]).grid(row=row, column=2)
            Label(parent, text='->').grid(row=row, column=3)            
            Label(parent, text=table_dict['receiver'][indx]).grid(row=row, column=4)
            Button(parent, text='plot', command=lambda sender=val, receiver=table_dict['receiver'][indx], commodity=table_dict['commodity'][indx]: self.sender_receiver_action(sender, receiver, commodity, 'plot')).grid(row=row, column=5)
            Button(parent, text='export', command=lambda sender=val, receiver=table_dict['receiver'][indx], commodity=table_dict['commodity'][indx]: self.sender_receiver_action(sender, receiver, commodity, 'export')).grid(row=row, column=6)
            row += 1

    def get_transaction_sr(self, sender, receiver, commodity):
        sender_id = sender[sender.index('(')+1:sender.index(')')]
        receiver_id = receiver[receiver.index('(')+1:receiver.index(')')]
        t = self.cur.execute('SELECT sum(quantity), time FROM transactions INNER JOIN resources ON transactions.resourceid == resources.resourceid where senderid=%s and receiverid=%s and commodity="%s" GROUP BY transactions.time' %(sender_id, receiver_id, commodity)).fetchall()
        qt = []
        time = []
        for i in t:
            qt.append(i['sum(quantity)'])
            time.append(i['time'])
        x = []
        y = []
        for i in range(self.duration):
            x.append(i)
            if i in time:
                indx = time.index(i)
                y.append(qt[indx])
            else:
                y.append(0)
        return x, y

    def sender_receiver_action(self, sender, receiver, commodity, action):
        sender_name = sender[:sender.index('(')]
        receiver_name = receiver[:receiver.index('(')]
        x, y = self.get_transaction_sr(sender, receiver, commodity)
        #! maybe combine these two later on

        if action == 'plot':
            fig = plt.figure()
            ax1 = fig.add_subplot(111)
            ax2 = ax1.twiny()
            ax1.plot(self.timestep_to_date(x), y)
            ax1.set_xlabel('Date')
            new_tick_locations = np.array([.1, .3, .5, .7, .9])
            ax2.set_xticks(new_tick_locations)
            l = new_tick_locations * max(x)
            l = ['%.0f' %z for z in l]
            print(l)
            ax2.set_xticklabels(l)
            ax2.set_xlabel('Timesteps')
            plt.ylabel('%s sent' %commodity)
            plt.grid()
            plt.tight_layout()
            plt.show()
        elif action == 'export':
            export_dir = os.path.join(self.output_path, 'exported_csv')
            if not os.path.exists(export_dir):
                os.mkdir(export_dir)
            filename = os.path.join(export_dir, '%s_%s_%s.csv' %(sender_name, receiver_name, commodity))
            s = 'time, quantity\n'
            for indx, val in enumerate(x):
                s += '%s, %s\n' %(str(x[indx]), str(y[indx]))
            with open(filename, 'w') as f:
                f.write(s)
            print('Exported %s' %filename)
            messagebox.showinfo('Success', 'Exported %s' %filename)


    def commodity_transfer_window(self):
        self.guide_text = ''
        self.commodity_tr_window = Toplevel(self.master)
        self.commodity_tr_window.title('Commodity Movement Window')
        self.commodity_tr_window.geometry('+700+1000')
        parent = self.commodity_tr_window
        
        commods = self.cur.execute('SELECT DISTINCT commodity FROM transactions').fetchall()
        names = []
        for i in commods:
            names.append(i['commodity'])
        if len(commods) > 30:
            canvas = Canvas(self.commodity_tr_window, width=800, height=1000)
            frame = Frame(canvas)
            scrollbar = Scrollbar(self.commodity_tr_window, command=canvas.yview)
            scrollbar.pack(side=RIGHT, fill='y')
            canvas.pack(side=LEFT, fill='both', expand=True)        
            def on_configure(event):
                canvas.configure(scrollregion=canvas.bbox('all'))
            canvas.configure(yscrollcommand=scrollbar.set)
            frame.bind('<Configure>', on_configure)
        
            canvas.create_window((4,4), window=frame, anchor='nw')
            parent = frame

        columnspan = 3
        
        Label(parent, text='List of Commodities').grid(row=0, columnspan=columnspan)
        Label(parent, text='======================').grid(row=1, columns=columnspan)
        row = 2
        for i in names:
            Label(parent, text=i).grid(row=row, column=0)
            Button(parent, text='plot', command=lambda commod=i: self.commodity_transfer_action(commod, 'plot')).grid(row=row, column=1)
            Button(parent, text='export', command=lambda commod=i: self.commodity_transfer_action(commod, 'export')).grid(row=row, column=2)
            row += 1

    def commodity_transfer_action(self, commod, action):
        movement = self.cur.execute('SELECT time, sum(quantity) FROM transactions INNER JOIN resources on transactions.resourceid==resources.resourceid WHERE commodity="%s" GROUP BY time' %commod).fetchall()
        qt = []
        time = []
        for i in movement:
            qt.append(i['sum(quantity)'])
            time.append(i['time'])
        x = []
        y = []
        for i in range(self.duration):
            x.append(i)
            if i in time:
                indx = time.index(i)
                y.append(qt[indx])
            else:
                y.append(0)

        if action == 'plot':
            fig = plt.figure()
            ax1 = fig.add_subplot(111)
            ax2 = ax1.twiny()
            ax1.plot(self.timestep_to_date(x), y)
            ax1.set_xlabel('Date')
            new_tick_locations = np.array([.1, .3, .5, .7, .9])
            ax2.set_xticks(new_tick_locations)
            l = new_tick_locations * max(x)
            l = ['%.0f' %z for z in l]
            print(l)
            ax2.set_xticklabels(l)
            ax2.set_xlabel('Timesteps')
            plt.ylabel('%s sent' %commod)
            plt.grid()
            plt.tight_layout()
            plt.show()
        elif action == 'export':
            export_dir = os.path.join(self.output_path, 'exported_csv')
            if not os.path.exists(export_dir):
                os.mkdir(export_dir)
            filename = os.path.join(export_dir, '%s.csv' %(commod))
            s = 'time, quantity\n'
            for indx, val in enumerate(x):
                s += '%s, %s\n' %(str(x[indx]), str(y[indx]))
            with open(filename, 'w') as f:
                f.write(s)
            print('Exported %s' %filename)
            messagebox.showinfo('Success', 'Exported %s' %filename)



    def agent_deployment_window(self):
        """
        plots / exports prototype entry and exit
        """
        self.guide_text = ''

        self.agent_dep_window = Toplevel(self.master)
        self.agent_dep_window.title('Agent Deployment / Exit Window')
        self.agent_dep_window.geometry('+700+1000')
        parent = self.agent_dep_window
        # s = bwidget.ScrolledWindow(self.agent_dep_window, auto='vertical', scrollbar='vertical')
        # f = bwidget.ScrollableFrame(s, constrainedwidth=True)
        # g = f.getframe()




        entry = self.cur.execute('SELECT DISTINCT prototype FROM agententry WHERE kind="Facility"').fetchall()
        proto_list = []
        for i in entry:
            proto_list.append(i['prototype'])
        if len(entry) > 30:
            canvas = Canvas(self.agent_dep_window, width=800, height=1000)
            frame = Frame(canvas)
            scrollbar = Scrollbar(self.agent_dep_window, command=canvas.yview)
            scrollbar.pack(side=RIGHT, fill='y')
            canvas.pack(side=LEFT, fill='both', expand=True)        
            def on_configure(event):
                canvas.configure(scrollregion=canvas.bbox('all'))
            canvas.configure(yscrollcommand=scrollbar.set)
            frame.bind('<Configure>', on_configure)
            
            canvas.create_window((4,4), window=frame, anchor='nw')
            parent = frame

        columnspan = 7
        

        Label(parent, text='List of Agents').grid(row=0, columnspan=columnspan)
        Label(parent, text='======================').grid(row=1, columnspan=columnspan)
        row = 2
        for i in proto_list:
            Label(parent, text=i).grid(row=row, column=0)
            Button(parent, text='plot enter', command=lambda prototype=i : self.agent_deployment_action(prototype, 'plot', 'enter')).grid(row=row, column=1)
            Button(parent, text='plot exit', command=lambda prototype=i : self.agent_deployment_action(prototype, 'plot', 'exit')).grid(row=row, column=2)
            Button(parent, text='plot deployed', command=lambda prototype=i : self.agent_deployment_action(prototype, 'plot', 'deployed')).grid(row=row, column=3)
            Button(parent, text='export enter', command=lambda prototype=i: self.agent_deployment_action(prototype, 'export', 'enter')).grid(row=row, column=4)
            Button(parent, text='export exit', command=lambda prototype=i: self.agent_deployment_action(prototype, 'export', 'exit')).grid(row=row, column=5)
            Button(parent, text='export deployed', command=lambda prototype=i: self.agent_deployment_action(prototype, 'export', 'deployed')).grid(row=row, column=6)
            row += 1


    def agent_deployment_action(self, prototype, action, which):
        entry = self.cur.execute('SELECT agentid, entertime FROM agententry WHERE prototype="%s"' %prototype).fetchall()
        agent_id_list = []
        entertime = []
        for i in entry:
            entertime.append(i['entertime'])
            agent_id_list.append(i['agentid'])
        exittime = []
        for i in agent_id_list:
            try:
                exit = self.cur.execute('SELECT agentid, exittime FROM agentexit WHERE agentid=%s' %str(i)).fetchone()
            except:
                # agentexit table doesn't exist
                continue
            if exit == None:
                exittime.append(-1)
            else:
                exittime.append(exit['exittime'])
        x = np.array(list(range(self.duration)))
        y = []
        if which == 'enter':
            for time in x:
                y.append(entertime.count(time))
        elif which == 'exit':
            for time in x:
                y.append(exittime.count(time))
        elif which == 'deployed':
            deployed = 0
            for time in x:
                deployed += entertime.count(time)
                deployed -= exittime.count(time)
                y.append(deployed)

        if action == 'plot':
            fig = plt.figure()
            ax1 = fig.add_subplot(111)
            ax2 = ax1.twiny()
            ax1.plot(self.timestep_to_date(x), y)
            ax1.set_xlabel('Date')
            new_tick_locations = np.array([.1, .3, .5, .7, .9])
            ax2.set_xticks(new_tick_locations)
            l = new_tick_locations * max(x)
            l = ['%.0f' %z for z in l]
            print(l)
            ax2.set_xticklabels(l)
            ax2.set_xlabel('Timesteps')
            plt.ylabel('Number of %s (%s)' %(prototype, which))
            plt.grid()
            plt.tight_layout()
            plt.show()
        elif action == 'export':
            export_dir = os.path.join(self.output_path, 'exported_csv')
            if not os.path.exists(export_dir):
                os.mkdir(export_dir)
            filename = os.path.join(export_dir, '%s_%s.csv' %(prototype, which))
            s = 'time, %s\n' %which
            for indx, val in enumerate(x):
                s += '%s, %s\n' %(str(x[indx]), str(y[indx]))
            with open(filename, 'w') as f:
                f.write(s)
            print('Exported %s' %filename)
            messagebox.showinfo('Success', 'Exported %s' %filename)


    def timeseries_window(self):
        z =0 



    def timestep_to_date(self, timestep):
        timestep = np.array(timestep) 
        month = self.init_month + timestep
        year = self.init_year + month//12
        month = month%12
        dates = [x+(y/12) for x, y in zip(year, month)]
        return dates
    
    
    def guide(self):
        self.guide_window = Toplevel(self.master)
        self.guide_window.title('Backend Analysis Guide')
        self.guide_window.geometry('+0+400')
        self.guide_text = """
        Here you can perform backend analysis of the Cyclus run.

        For more advanced users, you can navigate the tables yourself,
        using a sql query.

        For more beginner-level users, you can use the get material
        flow to obtain material flow, composition, etc for between
        facilities.

        """

        Label(self.guide_window, textvariable=self.guide_text, justify=LEFT).pack(padx=30, pady=30)
