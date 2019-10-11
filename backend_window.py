from tkinter import *
from PIL import Image, ImageTk
from tkinter import messagebox
from tkinter import filedialog
from tkinter.scrolledtext import ScrolledText
import xml.etree.ElementTree as et
import xmltodict
import uuid
import os
import seaborn as sns
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
        self.view_hard_limit = 100
        self.scroll_limit = 30
        self.el_z_dict = {'H': 1, 'He': 2, 'Li': 3, 'Be': 4, 'B': 5, 'C': 6, 'N': 7, 'O': 8, 'F': 9, 'Ne': 10, 'Na': 11, 'Mg': 12, 'Al': 13, 'Si': 14, 'P': 15, 'S': 16, 'Cl': 17, 'Ar': 18, 'K': 19, 'Ca': 20, 'Sc': 21, 'Ti': 22, 'V': 23, 'Cr': 24, 'Mn': 25, 'Fe': 26, 'Co': 27, 'Ni': 28, 'Cu': 29, 'Zn': 30, 'Ga': 31, 'Ge': 32, 'As': 33, 'Se': 34, 'Br': 35, 'Kr': 36, 'Rb': 37, 'Sr': 38, 'Y': 39, 'Zr': 40, 'Nb': 41, 'Mo': 42, 'Tc': 43, 'Ru': 44, 'Rh': 45, 'Pd': 46, 'Ag': 47, 'Cd': 48, 'In': 49, 'Sn': 50, 'Sb': 51, 'Te': 52, 'I': 53, 'Xe': 54, 'Cs': 55, 'Ba': 56, 'La': 57, 'Ce': 58, 'Pr': 59, 'Nd': 60, 'Pm': 61, 'Sm': 62, 'Eu': 63, 'Gd': 64, 'Tb': 65, 'Dy': 66, 'Ho': 67, 'Er': 68, 'Tm': 69, 'Yb': 70, 'Lu': 71, 'Hf': 72, 'Ta': 73, 'W': 74, 'Re': 75, 'Os': 76, 'Ir': 77, 'Pt': 78, 'Au': 79, 'Hg': 80, 'Tl': 81, 'Pb': 82, 'Bi': 83, 'Po': 84, 'At': 85, 'Rn': 86, 'Fr': 87, 'Ra': 88, 'Ac': 89, 'Th': 90, 'Pa': 91, 'U': 92, 'Np': 93, 'Pu': 94, 'Am': 95, 'Cm': 96, 'Bk': 97, 'Cf': 98, 'Es': 99, 'Fm': 100, 'Md': 101, 'No': 102, 'Lr': 103}

        Label(self.master, text='Choose backend analysis type:').pack()

        raw_table_button = Button(self.master, text='Navigate Raw Tables', command=lambda : self.view_raw_tables())
        raw_table_button.pack()

        material_flow_button = Button(self.master, text='Get Material Flow', command=lambda : self.material_flow_selection())
        material_flow_button.pack()

        commodity_transfer_button = Button(self.master, text='Get Commodity Flow', command=lambda : self.commodity_transfer_window())
        commodity_transfer_button.pack()

        deployment_of_agents_button = Button(self.master, text='Get Prototype Deployment', command=lambda : self.agent_deployment_window())
        deployment_of_agents_button.pack()

        facility_inventory_button = Button(self.master, text='Get Facility Inventory', command=lambda : self.facility_inventory_window())
        facility_inventory_button.pack()

        timeseries_button = Button(self.master, text='Get Timeseries', command=lambda : self.timeseries_window())
        timeseries_button.pack()


    def get_start_times(self):
        i = self.cur.execute('SELECT * FROM info').fetchone()
        self.init_year = i['InitialYear']
        self.init_month = i['InitialMonth']
        self.duration = i['Duration']
        i = self.cur.execute('SELECT * FROM TimeStepDur').fetchone()
        self.dt = i['DurationSecs']


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
        self.raw_table_window.title('Navigate Raw Tables')
        self.raw_table_window.geometry('+0+3500')
        # just like a sql query with ability to export and stuff
        self.guide_text = ''


    def material_flow_selection(self):
        self.guide_text = ''
        self.mat_selec_window = Toplevel(self.master)
        self.mat_selec_window.title('Which Selection')
        self.mat_selec_window.geometry('+700+1000')
        parent = self.mat_selec_window
        Label(parent, text='Group by agent or prototype').pack()
        Button(parent, text='Group by agent', command=lambda: self.view_material_flow(groupby='agent')).pack()
        Button(parent, text='Group by prototype', command=lambda: self.view_material_flow(groupby='prototype')).pack() 



    def view_material_flow(self, groupby):
        self.guide_text = ''
        # show material trade between prototypes
        self.material_flow_window = Toplevel(self.master)
        self.material_flow_window.title('List of transactions to view')
        self.material_flow_window.geometry('+700+1000')
        parent = self.material_flow_window

        traders = self.cur.execute('SELECT DISTINCT senderid, receiverid, commodity FROM transactions').fetchall()
        if groupby == 'agent':
            table_dict = {'sender': [],
                          'receiver': [],
                          'commodity': []}

            parent = self.assess_scroll_deny(len(traders), self.material_flow_window)
            if parent == -1:
                return

            # create table of sender - receiverid - commodity set like:
            for i in traders:
                table_dict['sender'].append(self.id_proto_dict[i['senderid']] + '(%s)' %str(i['senderid']))
                table_dict['receiver'].append(self.id_proto_dict[i['receiverid']] + '(%s)' %str(i['receiverid']))
                table_dict['commodity'].append(i['commodity'])
        elif groupby == 'prototype':
            already = []
            table_dict = {'sender': [], 'receiver': [], 'commodity': []}
            for i in traders:
                checker = [self.id_proto_dict[i['senderid']], self.id_proto_dict[i['receiverid']], i['commodity']]
                if checker in already:
                    continue
                else:
                    already.append(checker)
                    table_dict['sender'].append(checker[0])
                    table_dict['receiver'].append(checker[1])
                    table_dict['commodity'].append(checker[2])
            parent = self.assess_scroll_deny(len(table_dict['sender']), self.material_flow_window)
            if parent == -1:
                return

        columnspan = 7
        Label(parent, text='List of transactions:').grid(row=0, columnspan=columnspan)
        Label(parent, text='Get top ').grid(row=1, column=0)
        self.n_isos = Entry(parent)
        self.n_isos.grid(row=1, column=1)
        Label(parent, text='Isotopes').grid(row=1, column=2)
        if groupby == 'agent':
            Label(parent, text='Sender (id)').grid(row=2, column=0)
            Label(parent, text='Receiver (id)').grid(row=2, column=4)
        else:
            Label(parent, text='Sender').grid(row=2, column=0)
            Label(parent, text='Receiver').grid(row=2, column=4)
        Label(parent, text='').grid(row=2, column=1)
        Label(parent, text='Commodity').grid(row=2, column=2)
        Label(parent, text='').grid(row=2, column=3)
        Label(parent, text=' ').grid(row=2, column=5)
        Label(parent, text='======================').grid(row=3, columnspan=columnspan)
             
        row = 4
        for indx, val in enumerate(table_dict['sender']):
            Label(parent, text=val).grid(row=row, column=0)
            Label(parent, text='->').grid(row=row, column=1)
            Label(parent, text=table_dict['commodity'][indx]).grid(row=row, column=2)
            Label(parent, text='->').grid(row=row, column=3)            
            Label(parent, text=table_dict['receiver'][indx]).grid(row=row, column=4)
            Button(parent, text='plot', command=lambda sender=val, receiver=table_dict['receiver'][indx], commodity=table_dict['commodity'][indx], groupby=groupby: self.sender_receiver_action(sender, receiver, commodity, 'plot', groupby)).grid(row=row, column=5)
            Button(parent, text='export', command=lambda sender=val, receiver=table_dict['receiver'][indx], commodity=table_dict['commodity'][indx], groupby=groupby: self.sender_receiver_action(sender, receiver, commodity, 'export', groupby)).grid(row=row, column=6)
            row += 1



    def sender_receiver_action(self, sender, receiver, commodity, action, groupby):
        n_isos = self.check_n_isos()
        if n_isos == -1:
            return

        if groupby == 'prototype':
            receiver_id = [k for k,v in self.id_proto_dict.items() if v == receiver] 
            sender_id = [k for k,v in self.id_proto_dict.items() if v == sender]
        else:
            sender_name = sender[:sender.index('(')]
            receiver_name = receiver[:receiver.index('(')]
            sender_id = [sender[sender.index('(')+1:sender.index(')')]]
            receiver_id = [receiver[receiver.index('(')+1:receiver.index(')')]]
        
        #!#!#!#!
        str_sender_id = [str(q) for q in sender_id]
        str_receiver_id = [str(q) for q in receiver_id]
        if n_isos == 0:
            query = 'SELECT sum(quantity), time FROM transactions INNER JOIN resources ON transactions.resourceid == resources.resourceid WHERE (senderid = ' + ' OR senderid = '.join(str_sender_id) + ') AND (receiverid = ' + ' OR receiverid = '.join(str_receiver_id) + ') GROUP BY time'
            q = self.cur.execute(query).fetchall()
            x, y = self.query_result_to_timeseries(q, 'sum(quantity)')
        else:
            query = 'SELECT sum(quantity)*massfrac, nucid, time FROM transactions INNER JOIN resources ON transactions.resourceid == resources.resourceid LEFT OUTER JOIN compositions ON compositions.qualid = resources.qualid WHERE (senderid = ' + ' OR senderid = '.join(str_sender_id) + ') AND (receiverid = ' + ' OR receiverid = '.join(str_receiver_id) + ') GROUP BY time, nucid'
            q = self.cur.execute(query).fetchall()
            x, y = self.query_result_to_dict(q, 'nucid', 'sum(quantity)*massfrac', n_isos)

        if action == 'plot':
            self.plot(x, y, '%s Sent' %commodity)
        elif action == 'export':
            if groupby == 'prototype':
                self.export(x, y, '%s_%s_%s.csv' %(sender, receiver, commodity))
            else:
                self.export(x, y, '%s_%s_%s.csv' %(sender_name, receiver_name, commodity))
            

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
        names.sort(key=str.lower)
        parent = self.assess_scroll_deny(len(commods), self.commodity_tr_window)
        if parent == -1:
            return

        columnspan = 3
        
        Label(parent, text='List of Commodities').grid(row=0, columnspan=columnspan)
        Label(parent, text='======================').grid(row=1, columns=columnspan)
        Label(parent, text='Get top ').grid(row=2, column=0)
        self.n_isos = Entry(parent)
        self.n_isos.grid(row=2, column=1)
        Label(parent, text='Isotopes').grid(row=2, column=2)
        row = 3
        for i in names:
            Label(parent, text=i).grid(row=row, column=0)
            Button(parent, text='plot', command=lambda commod=i: self.commodity_transfer_action(commod, 'plot')).grid(row=row, column=1)
            Button(parent, text='export', command=lambda commod=i: self.commodity_transfer_action(commod, 'export')).grid(row=row, column=2)
            row += 1

    def commodity_transfer_action(self, commod, action):
        movement = self.cur.execute('SELECT time, sum(quantity) FROM transactions INNER JOIN resources on transactions.resourceid==resources.resourceid WHERE commodity="%s" GROUP BY time' %commod).fetchall()
        x, y = self.query_result_to_timeseries(movement, 'sum(quantity)')

        if action == 'plot':
            self.plot(x, y, '%s Sent' %commod)
        elif action == 'export':
            self.export(x, y, '%s.csv' %commod)


    def agent_deployment_window(self):
        """
        plots / exports prototype entry and exit
        """
        self.guide_text = ''

        self.agent_dep_window = Toplevel(self.master)
        self.agent_dep_window.title('Prototype Deployment / Exit Window')
        self.agent_dep_window.geometry('+700+1000')
        parent = self.agent_dep_window
        # s = bwidget.ScrolledWindow(self.agent_dep_window, auto='vertical', scrollbar='vertical')
        # f = bwidget.ScrollableFrame(s, constrainedwidth=True)
        # g = f.getframe()

        entry = self.cur.execute('SELECT DISTINCT prototype FROM agententry WHERE kind="Facility"').fetchall()
        proto_list = [i['prototype'] for i in entry]
        proto_list.sort(key=str.lower)
        parent = self.assess_scroll_deny(len(entry), self.agent_dep_window)
        if parent == -1:
            return

        columnspan = 7
        

        Label(parent, text='List of Agents').grid(row=0, columnspan=columnspan)
        Label(parent, text='======================').grid(row=1, columnspan=columnspan)
        Label(parent, text='=====Plot=====').grid(row=2, columnspan=3)
        Label(parent, text='=====Export=====').grid(row=2, column=4, columnspan=3)
        row = 3
        for i in proto_list:
            Label(parent, text=i).grid(row=row, column=3)
            Button(parent, text='enter', command=lambda prototype=i : self.agent_deployment_action(prototype, 'plot', 'enter')).grid(row=row, column=0)
            Button(parent, text='exit', command=lambda prototype=i : self.agent_deployment_action(prototype, 'plot', 'exit')).grid(row=row, column=1)
            Button(parent, text='deployed', command=lambda prototype=i : self.agent_deployment_action(prototype, 'plot', 'deployed')).grid(row=row, column=2)
            Button(parent, text='enter', command=lambda prototype=i: self.agent_deployment_action(prototype, 'export', 'enter')).grid(row=row, column=4)
            Button(parent, text='exit', command=lambda prototype=i: self.agent_deployment_action(prototype, 'export', 'exit')).grid(row=row, column=5)
            Button(parent, text='deployed', command=lambda prototype=i: self.agent_deployment_action(prototype, 'export', 'deployed')).grid(row=row, column=6)
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
            self.plot(x, y, 'Number of %s (%s)' %(prototype, which))
        elif action == 'export':
            self.export(x, y, '%s_%s.csv' %(prototype, which))


    def timeseries_window(self):
        self.guide_text = ''
        self.ts_window = Toplevel(self.master)
        self.ts_window.title('Timeseries Window')
        self.ts_window.geometry('+700+1000')
        parent = self.ts_window

        tables = self.cur.execute('SELECT name FROM sqlite_master WHERE type="table"').fetchall()
        timeseries_tables_list = []
        for i in tables:
            if 'TimeSeries' in i['name']:
                timeseries_tables_list.append(i['name'].replace('TimeSeries', ''))
        timeseries_tables_list.sort()
        parent = self.assess_scroll_deny(len(tables), self.ts_window)
        if parent == -1:
            return

        columnspan = 2
        Label(parent, text='List of Timeseries').grid(row=0, columnspan=columnspan)
        Label(parent, text='======================').grid(row=1, columns=columnspan)
        row = 2

        for i in timeseries_tables_list:
            Label(parent, text=i).grid(row=row, column=0)
            Button(parent, text='more', command=lambda timeseries=i: self.timeseries_action(timeseries)).grid(row=row, column=1)
            row += 1

    def timeseries_action(self, timeseries):
        agentid_list_q = self.cur.execute('SELECT distinct agentid FROM TimeSeries%s' %timeseries).fetchall()
        agentid_list = [i['agentid'] for i in agentid_list_q]
        agentname_list = [self.id_proto_dict[i] for i in agentid_list]
        self.ta_window = Toplevel(self.ts_window)
        self.ta_window.title('%s Timeseries Window' %timeseries.capitalize())
        self.ta_window.geometry('+1000+1000')
        parent = self.ta_window

        parent = self.assess_scroll_deny(len(agentname_list), self.ta_window)
        if parent == -1:
            return
        
        columnspan = 3
        Label(parent, text='Agents that reported %s' %timeseries).grid(row=0, columnspan=columnspan)
        Label(parent, text='======================').grid(row=1, columns=columnspan)
        row = 2
        Label(parent, text='Aggregate sum').grid(row=row, column=0)
        Button(parent, text='plot', command=lambda timeseries=timeseries, agentid='agg', action='plot': self.timeseries_action_action(timeseries, agentid, action)).grid(row=row, column=1)
        Button(parent, text='export', command=lambda timeseries=timeseries, agentid='agg', action='export': self.timeseries_action_action(timeseries, agentid, action)).grid(row=row, column=2)
        row = 3
        for indx, i in enumerate(agentname_list):
            Label(parent, text='%s (%s)' %(i, agentid_list[indx])).grid(row=row, column=0)
            Button(parent, text='plot', command=lambda timeseries=timeseries, agentid=agentid_list[indx], action='plot': self.timeseries_action_action(timeseries, agentid, action)).grid(row=row, column=1)
            Button(parent, text='export', command=lambda timeseries=timeseries, agentid=agentid_list[indx], action='export': self.timeseries_action_action(timeseries, agentid, action)).grid(row=row, column=2)
            row += 1
            
       
    def timeseries_action_action(self, timeseries, agentid, action):
        if agentid == 'agg':
            series_q = self.cur.execute('SELECT time, sum(value) FROM TimeSeries%s GROUP BY time' %timeseries).fetchall()
        else:
            series_q = self.cur.execute('SELECT time, sum(value) FROM TimeSeries%s WHERE agentid=%s GROUP BY time' %(timeseries, str(agentid))).fetchall()
        x, y = self.query_result_to_timeseries(series_q, 'sum(value)')

        if action == 'plot':
            self.plot(x, y, '%s Timeseries' %timeseries)
        elif action == 'export':
            if agentid == 'agg':
                name = '%s_aggregate_timeseries.csv' % timeseries
            else:
                name = '%s_%s_timeseries.csv' %(self.id_proto_dict[agentid], timeseries)
            self.export(x, y, name)


    def facility_inventory_window(self):
        # check if explicit inventory is okay

        isit = self.cur.execute('SELECT * FROM InfoExplicitInv').fetchone()
        if not isit['RecordInventory']:
            messagebox.showerror('Dont have it', 'This simulation was run without `explicit_inventory` turned on in the simulation definition. Turn that on and run the simulation again to view the inventory.')
            return

        self.guide_text = ''
        # show material trade between prototypes
        self.inv_window = Toplevel(self.master)
        self.inv_window.title('Which Selection')
        self.inv_window.geometry('+700+1000')
        parent = self.inv_window
        Label(parent, text='Group by agent or prototype:').pack()
        Button(parent, text='Group by agent', command=lambda: self.inv_inv_window(groupby='agent')).pack()
        Button(parent, text='Group by prototype', command=lambda: self.inv_inv_window(groupby='prototype')).pack()

    def inv_inv_window(self, groupby):
        self.guide_text = ''
        # show material trade between prototypes
        self.inv_inv_window = Toplevel(self.inv_window)
        self.inv_inv_window.title('Groupby %s' %groupby)
        self.inv_inv_window.geometry('+1000+1000')
        parent = self.inv_inv_window
        if groupby == 'agent':
            parent = self.assess_scroll_deny(len(self.id_proto_dict.keys()), self.inv_inv_window)
            if parent == -1:
                return

            # show the list of all agents to display
            columnspan = 3
            Label(parent, text='List of Agents').grid(row=0, columnspan=columnspan)
            Label(parent, text='Agent (id)').grid(row=1, column=0)
            Label(parent, text='======================').grid(row=2, columnspan=columnspan)
            Label(parent, text='Get top ').grid(row=3, column=0)
            self.n_isos = Entry(parent)
            self.n_isos.grid(row=3, column=1)
            Label(parent, text='Isotopes').grid(row=3, column=2)
            row = 4
            for id_, proto_ in self.id_proto_dict.items():
                Label(parent, text= '%s (%s)' %(proto_, id_)).grid(row=row, column=0)
                Button(parent, text='plot', command=lambda id_list=[id_]: self.inv_action(id_list, 'plot')).grid(row=row, column=1)
                Button(parent, text='export', command=lambda id_list=[id_]: self.inv_action(id_list, 'export')).grid(row=row, column=2)
                row += 1 
        
        elif groupby == 'prototype':
            # show the list of prototypes to display
            entry = self.cur.execute('SELECT DISTINCT prototype FROM agententry WHERE kind="Facility"').fetchall()
            proto_list = [i['prototype'] for i in entry]
            proto_list.sort(key=str.lower)

            parent = self.assess_scroll_deny(len(self.id_proto_dict.keys()), self.inv_inv_window)
            if parent == -1:
                return
            
            row = 0
            for i in proto_list:
                id_list = [k for k,v in self.id_proto_dict.items() if v == i]
                Label(parent, text= '%s' %i).grid(row=row, column=0)
                Button(parent, text='plot', command=lambda id_list=id_list: self.inv_action(id_list, 'plot')).grid(row=row, column=1)
                Button(parent, text='export', command=lambda id_list=id_list: self.inv_action(id_list, 'export')).grid(row=row, column=2)
                row += 1


    def inv_action(self, id_list, action):
        str_id_list = [str(q) for q in id_list]
        query = 'SELECT sum(quantity), time FROM ExplicitInventory WHERE (agentid = ' + ' OR agentid = '.join(str_id_list) + ') GROUP BY time'
        q = self.cur.execute(query).fetchall()
        x, y = self.query_result_to_timeseries(q, 'sum(quantity)')
        name = self.id_proto_dict[id_list[0]]
        if action == 'plot':
            self.plot(x, y, '%s Inventory' %name)
        elif action == 'export':
            self.export(x, y, '%s_inv.csv' %name)
        

    # helper functions

    def plot(self, x, y, ylabel, xlabel='Date'):
        fig = plt.figure()
        ax1 = fig.add_subplot(111)
        ax2 = ax1.twiny()
        lines = []
        if type(y) is dict:
            for key, val in y.items():
                try: # if nucid, turn to nameAAA
                    e = int(key) // 10000
                    a = e % 1000
                    z = e // 1000
                    for k, v in self.el_z_dict.items():
                        if v == z:
                            name = k
                    key = name + str(a)
                except:
                    z = 0
                l, = ax1.plot(self.timestep_to_date(x), val, label=key)
                lines.append(l)
            if sum(sum(y[k]) for k in y) > 1e3:
                ax1 = plt.gca()
                ax1.get_yaxis().set_major_formatter(
                    plt.FuncFormatter(lambda x, loc: "{:,}".format(int(x))))
        else:
            ax1.plot(self.timestep_to_date(x), y, label=ylabel)
            if max(y) > 1e3:
                ax1 = plt.gca()
                ax1.get_yaxis().set_major_formatter(
                    plt.FuncFormatter(lambda x, loc: "{:,}".format(int(x))))
        ax1.set_xlabel(xlabel)
        new_tick_locations = np.array([.1, .3, .5, .7, .9])
        ax2.set_xticks(new_tick_locations)
        l = new_tick_locations * max(x)
        l = ['%.0f' %z for z in l]
        print(l)
        ax2.set_xticklabels(l)
        ax2.set_xlabel('Timesteps')
        ax1.legend(handles=lines)
        plt.ylabel(ylabel)
        plt.grid()
        plt.tight_layout()
        plt.show()


    def export(self, x, y, filename):
        export_dir = os.path.join(self.output_path, 'exported_csv')
        if not os.path.exists(export_dir):
            os.mkdir(export_dir)
        filename = os.path.join(export_dir, filename)
        if type(y) is dict:
            s = 'time, %s\n' %', '.join(list(y.keys()))
            for indx, val in enumerate(x):
                s += '%s, %s\n' %(str(x[indx]), ', '.join([q[indx] for q in list(y.values())]))
        else:
            s = 'time, quantity\n'
            for indx, val in enumerate(x):
                s += '%s, %s\n' %(str(x[indx]), str(y[indx]))
        with open(filename, 'w') as f:
            f.write(s)
        print('Exported %s' %filename)
        messagebox.showinfo('Success', 'Exported %s' %filename)


    def timestep_to_date(self, timestep):
        timestep = np.array(timestep) 
        month = self.init_month + (timestep * (self.dt / 2629846))
        year = self.init_year + month//12
        month = month%12
        dates = [x+(y/12) for x, y in zip(year, month)]
        return dates


    def query_result_to_timeseries(self, query_result, col_name,
                                   time_col_name='time'):
        x = np.arange(self.duration)
        y = np.zeros(self.duration)
        for i in query_result:
            y[int(i[time_col_name])] += i[col_name]
        return x, y

    def query_result_to_dict(self, query_result, vary_col_name, val_col,
                             time_col_name='time', topn=10):
        x = np.arange(self.duration)
        y = {}
        keys = list(set([q[vary_col_name] for q in query_result]))
        for i in keys:
            y[i] = np.zeros(self.duration)
        for i in query_result:
            y[i[vary_col_name]] += i[val_col]
        y1 = {k:np.mean(v) for k, v in y.items()}
        keys = sorted(y1, key=y1.__getitem__, reverse=True)[:topn]
        new_y = {k:v for k, v in y.items() if k in keys}
        return x, new_y


    def aggregate_dates(self, x, y, agg_dt):
        # roughly aggregates
        groups = int(self.agg_dt / self.dt)
        new_x = np.arange(self.duration / groups)
        new_y = []


    def assess_scroll_deny(self, length, window_obj):
        if length > self.view_hard_limit:
            messagebox.showinfo('Too much', 'You have %s distinct values. Too much to show here.' %length)
            window_obj.destroy()
            return -1
        elif length > self.scroll_limit:
            return self.add_scrollbar(window_obj)
        else:
            return window_obj

    def add_scrollbar(self, window_obj):
        canvas = Canvas(window_obj, width=800, height=1000)
        frame = Frame(canvas)
        scrollbar = Scrollbar(window_obj, command=canvas.yview)
        scrollbar.pack(side=RIGHT, fill='y')
        canvas.pack(side=LEFT, fill='both', expand=True)        
        def on_configure(event):
            canvas.configure(scrollregion=canvas.bbox('all'))
        canvas.configure(yscrollcommand=scrollbar.set)
        frame.bind('<Configure>', on_configure)
        canvas.create_window((4,4), window=frame, anchor='nw')
        return frame

    def check_n_isos(self):
        if self.n_isos.get() == '':
            return 0
        try:
            return(int(self.n_isos.get()))
        except:
            messagebox.showerror('You put in %s for the number of isotopes\n It should be an integer' %self.n_isos)
            return -1

    
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
