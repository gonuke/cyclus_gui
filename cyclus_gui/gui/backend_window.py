from tkinter import *
from tkinter import messagebox
from tkinter import filedialog
from tkinter.scrolledtext import ScrolledText
import uuid
import os
import shutil
import json
import copy
import sqlite3 as lite
import networkx as nx
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import pandas as pd
from cyclus_gui.gui.window_tools import *


class BackendWindow(Frame):
    def __init__(self, master, output_path, filename='cyclus.sqlite'):
        """
        does backend analysis
        """
        self.screen_width = master.winfo_screenwidth()
        self.screen_height = master.winfo_screenheight()
        
        self.master = Toplevel(master)
        self.master.title('Backend Analysis')
        self.output_path = output_path
        self.master.geometry('+0+%s' %int(self.screen_height/4))
        self.configure_window()
        self.get_cursor(filename)
        self.get_id_proto_dict()
        self.get_start_times()


        self.metaguide()
        self.el_z_dict = {'H': 1, 'He': 2, 'Li': 3, 'Be': 4, 'B': 5, 'C': 6, 'N': 7, 'O': 8, 'F': 9, 'Ne': 10, 'Na': 11, 'Mg': 12, 'Al': 13, 'Si': 14, 'P': 15, 'S': 16, 'Cl': 17, 'Ar': 18, 'K': 19, 'Ca': 20, 'Sc': 21, 'Ti': 22, 'V': 23, 'Cr': 24, 'Mn': 25, 'Fe': 26, 'Co': 27, 'Ni': 28, 'Cu': 29, 'Zn': 30, 'Ga': 31, 'Ge': 32, 'As': 33, 'Se': 34, 'Br': 35, 'Kr': 36, 'Rb': 37, 'Sr': 38, 'Y': 39, 'Zr': 40, 'Nb': 41, 'Mo': 42, 'Tc': 43, 'Ru': 44, 'Rh': 45, 'Pd': 46, 'Ag': 47, 'Cd': 48, 'In': 49, 'Sn': 50, 'Sb': 51, 'Te': 52, 'I': 53, 'Xe': 54, 'Cs': 55, 'Ba': 56, 'La': 57, 'Ce': 58, 'Pr': 59, 'Nd': 60, 'Pm': 61, 'Sm': 62, 'Eu': 63, 'Gd': 64, 'Tb': 65, 'Dy': 66, 'Ho': 67, 'Er': 68, 'Tm': 69, 'Yb': 70, 'Lu': 71, 'Hf': 72, 'Ta': 73, 'W': 74, 'Re': 75, 'Os': 76, 'Ir': 77, 'Pt': 78, 'Au': 79, 'Hg': 80, 'Tl': 81, 'Pb': 82, 'Bi': 83, 'Po': 84, 'At': 85, 'Rn': 86, 'Fr': 87, 'Ra': 88, 'Ac': 89, 'Th': 90, 'Pa': 91, 'U': 92, 'Np': 93, 'Pu': 94, 'Am': 95, 'Cm': 96, 'Bk': 97, 'Cf': 98, 'Es': 99, 'Fm': 100, 'Md': 101, 'No': 102, 'Lr': 103}
        self.z_el_dict = {v:k for k, v in self.el_z_dict.items()}
        Label(self.master, text='Choose backend analysis type:').pack()

        # raw_table_button = Button(self.master, text='Navigate Raw Tables', command=lambda : self.view_raw_tables())
        # raw_table_button.pack()

        material_flow_plot = Button(self.master, text='Visualize Trade', command=lambda: self.plot_flow())
        material_flow_plot.pack()

        material_flow_button = Button(self.master, text='Get Material Flow', command=lambda : self.material_flow_selection())
        material_flow_button.pack()

        commodity_transfer_button = Button(self.master, text='Get Commodity Flow', command=lambda : self.commodity_transfer_window())
        commodity_transfer_button.pack()

        deployment_of_agents_button = Button(self.master, text='Get Facility Deployment', command=lambda : self.agent_deployment_window())
        deployment_of_agents_button.pack()

        facility_inventory_button = Button(self.master, text='Get Facility Inventory', command=lambda : self.facility_inventory_window())
        facility_inventory_button.pack()

        timeseries_button = Button(self.master, text='Get Timeseries', command=lambda : self.timeseries_window())
        timeseries_button.pack()

    def configure_window(self):
        self.config_window = Toplevel(self.master)
        self.config_window.title('Configuration')
        self.config_window.geometry('+%s+%s' %(int(self.screen_width/1.5), int(self.screen_height/3)))
        parent = self.config_window

        columnspan = 4
        self.config_dict = {}
        Label(parent, text='Configuration', bg='yellow').grid(row=0, columnspan=columnspan)
        # n_isos, plotting scale, nuclide notation
        Label(parent, text='Parameter', bg='pale green').grid(row=1, column=0)
        Label(parent, text='Value', bg='light salmon').grid(row=1, column=1)
        Label(parent, text='Description', bg='SkyBlue1').grid(row=1, column=2)
        
        Label(parent, text='Plot top n isos:').grid(row=2, column=0)
        self.config_dict['n_isos'] = Entry(parent)
        self.config_dict['n_isos'].grid(row=2, column=1)
        Label(parent, text='Leave it blank to plot/export mass').grid(row=2, column=2)

        Label(parent, text='Plot y Scale').grid(row=3, column=0)
        self.config_dict['y_scale'] = StringVar(self.config_window)
        choices = ['linear', 'log', 'symlog', 'logit']
        self.config_dict['y_scale'].set('linear')
        OptionMenu(self.config_window, self.config_dict['y_scale'], *choices).grid(row=3, column=1)
        # self.tkvar.trace('w', s)
        Label(parent, text='Scale of y scale').grid(row=3, column=2)

        Label(parent, text='Nuclide Notation').grid(row=4, column=0)
        self.config_dict['nuc_notation'] = StringVar(self.config_window)
        choices = ['ZZAAA', 'name']
        self.config_dict['nuc_notation'].set('ZZAAA')
        OptionMenu(self.config_window, self.config_dict['nuc_notation'], *choices).grid(row=4, column=1)
        Label(parent, text='nuclide notation in plot legend').grid(row=4, column=2)

        Label(parent, text='Filename Suffix').grid(row=5, column=0)
        self.config_dict['suffix'] = Entry(parent)
        self.config_dict['suffix'].grid(row=5, column=1)
        Label(parent, text='Append to filename for overlap prevention').grid(row=5, column=2)

        Label(parent, text='Cumulative').grid(row=6, column=0)
        self.config_dict['cumulative'] = StringVar(self.config_window)
        choices = ['True', 'False']
        self.config_dict['cumulative'].set('False')
        OptionMenu(self.config_window, self.config_dict['cumulative'], *choices).grid(row=6, column=1)
        Label(parent, text='Plot/Export cumulative values').grid(row=6, column=2)


    def print_choice(self):
        print(self.self.config_dict['y_scale'].get())

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


    def get_cursor(self, filename='cyclus.sqlite'):
        con = lite.connect(os.path.join(self.output_path, filename))
        con.row_factory = lite.Row
        self.cur = con.cursor()


    def view_raw_tables(self):
        self.raw_table_window = Toplevel(self.master)
        self.raw_table_window.title('Navigate Raw Tables')
        self.raw_table_window.geometry('+%s+%s' %(int(self.screen_width/4), int(self.screen_height/2)))

        # just like a sql query with ability to export and stuff
        self.guide('This not ready yet')


    def material_flow_selection(self):
        self.guide("""
            Material Flow:
            
            Material flow can be plotted/exported by agent or prototype
            
            agent: for each unique agent(id), you can select which
                transaction to plot / export
            prototype: for each unique prototype (agents with same
                prototypes are aggregated), you can select
                which transaction to plot / export""")
        self.mat_selec_window = Toplevel(self.master)
        self.mat_selec_window.title('Which Selection')
        self.mat_selec_window.geometry('+%s+%s' %(int(self.screen_width/9999), int(self.screen_height/2)))
        parent = self.mat_selec_window
        Label(parent, text='Group by agent or prototype', bg='yellow').pack()
        Button(parent, text='Group by agent', command=lambda: self.view_material_flow(groupby='agent')).pack()
        Button(parent, text='Group by prototype', command=lambda: self.view_material_flow(groupby='prototype')).pack() 



    def view_material_flow(self, groupby):
        # show material trade between prototypes
        self.material_flow_window = Toplevel(self.master)
        self.material_flow_window.title('List of transactions to view')
        self.material_flow_window.geometry('+%s+%s' %(int(self.screen_width/4), int(self.screen_height/2)))
        parent = self.material_flow_window

        traders = self.cur.execute('SELECT DISTINCT senderid, receiverid, commodity FROM transactions').fetchall()
        if groupby == 'agent':
            table_dict = {'sender': [],
                          'receiver': [],
                          'commodity': []}

            parent = assess_scroll_deny(len(traders), self.material_flow_window)
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
            parent = assess_scroll_deny(len(table_dict['sender']), self.material_flow_window)
            if parent == -1:
                return

        columnspan = 7
        Label(parent, text='List of transactions:', bg='yellow').grid(row=0, columnspan=columnspan)
        if groupby == 'agent':
            Label(parent, text='Sender (id)', bg='pale green').grid(row=1, column=0)
            Label(parent, text='Receiver (id)', bg='SkyBlue1').grid(row=1, column=4)
        else:
            Label(parent, text='Sender', bg='pale green').grid(row=1, column=0)
            Label(parent, text='Receiver', bg='SkyBlue1').grid(row=1, column=4)
        Label(parent, text='').grid(row=1, column=1)
        Label(parent, text='Commodity', bg='light salmon').grid(row=1, column=2)
        Label(parent, text='').grid(row=1, column=3)
        Label(parent, text=' ').grid(row=1, column=5)
        Label(parent, text='======================').grid(row=2, columnspan=columnspan)
             
        row = 3
        for indx, val in enumerate(table_dict['sender']):
            Label(parent, text=val, bg='pale green').grid(row=row, column=0)
            Label(parent, text='->').grid(row=row, column=1)
            Label(parent, text=table_dict['commodity'][indx], bg='light salmon').grid(row=row, column=2)
            Label(parent, text='->').grid(row=row, column=3)            
            Label(parent, text=table_dict['receiver'][indx], bg='SkyBlue1').grid(row=row, column=4)
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
            # query = 'SELECT sum(quantity)*massfrac, nucid, time FROM transactions INNER JOIN resources ON transactions.resourceid == resources.resourceid LEFT OUTER JOIN compositions ON compositions.qualid = resources.qualid WHERE (senderid = ' + ' OR senderid = '.join(str_sender_id) + ') AND (receiverid = ' + ' OR receiverid = '.join(str_receiver_id) + ') GROUP BY time, nucid'
            # q = self.cur.execute(query).fetchall()
            # x, y = self.query_result_to_dict(q, 'nucid', 'sum(quantity)*massfrac')
            x, y = self.get_iso_flow_dict('(senderid = ' + ' OR senderid = '.join(str_sender_id) + ') AND (receiverid = ' + ' OR receiverid = '.join(str_receiver_id) + ')', n_isos)

        if groupby == 'prototype':
            name = '%s_%s_%s.csv' %(sender, receiver, commodity)
        else:
            name = '%s_%s_%s.csv' %(sender_name, receiver_name, commodity)

        if action == 'plot':
            self.plot(x, y, '%s Sent' %commodity, name.replace('.csv', ''))
        elif action == 'export':
            self.export(x, y, name)
            

    def commodity_transfer_window(self):
        self.guide("""
            Commodity transfer:
            
            You can plot/export the aggregated transaction
            of all unique commodities. The direction of the movement
            is not taken into account.""")
        self.commodity_tr_window = Toplevel(self.master)
        self.commodity_tr_window.title('Commodity Movement Window')
        self.commodity_tr_window.geometry('+%s+%s' %(int(self.screen_width/4), int(self.screen_height/2)))
        parent = self.commodity_tr_window
        
        commods = self.cur.execute('SELECT DISTINCT commodity FROM transactions').fetchall()
        names = []
        for i in commods:
            names.append(i['commodity'])
        names.sort(key=str.lower)
        parent = assess_scroll_deny(len(commods), self.commodity_tr_window)
        if parent == -1:
            return

        columnspan = 3
        
        Label(parent, text='List of Commodities', bg='yellow').grid(row=0, columnspan=columnspan)
        Label(parent, text='======================').grid(row=1, columns=columnspan)
        row = 2
        for i in names:
            Label(parent, text=i, bg='pale green').grid(row=row, column=0)
            Button(parent, text='plot', command=lambda commod=i: self.commodity_transfer_action(commod, 'plot')).grid(row=row, column=1)
            Button(parent, text='export', command=lambda commod=i: self.commodity_transfer_action(commod, 'export')).grid(row=row, column=2)
            row += 1

    def commodity_transfer_action(self, commod, action):
        n_isos = self.check_n_isos()
        if n_isos == -1:
            return

        if n_isos == 0:
            movement = self.cur.execute('SELECT time, sum(quantity) FROM transactions INNER JOIN resources on transactions.resourceid==resources.resourceid WHERE commodity="%s" GROUP BY time' %commod).fetchall()
            x, y = self.query_result_to_timeseries(movement, 'sum(quantity)')
        else:
            # movement = self.cur.execute('SELECT time, sum(quantity)*massfrac, nucid FROM transactions INNER JOIN resources ON transactions.resourceid = resources.resourceid LEFT OUTER JOIN compositions ON compositions.qualid = resources.qualid WHERE commodity="%s" GROUP BY transactions.time, nucid' %commod).fetchall()
            # x, y = self.query_result_to_dict(movement, 'nucid', 'sum(quantity)*massfrac')
            x, y = self.get_iso_flow_dict('commodity = "%s"' %commod, n_isos)


        if action == 'plot':
            self.plot(x, y, '%s Sent', commod)
        elif action == 'export':
            self.export(x, y, '%s.csv' %commod)


    def get_iso_flow_dict(self, where_phrase, n_isos, time_col_name='Time'):
        q = self.cur.execute('SELECT time, quantity, resources.qualid, nucid, sum(quantity*massfrac) FROM transactions INNER JOIN resources ON transactions.resourceid = resources.resourceid INNER JOIN compositions on compositions.qualid = resources.qualid WHERE %s GROUP BY nucid, time' %where_phrase).fetchall()
        uniq_ = self.cur.execute('SELECT DISTINCT(nucid) FROM transactions INNER JOIN resources ON resources.resourceid = transactions.resourceid INNER JOIN compositions ON compositions.qualid = resources.qualid WHERE %s' %where_phrase).fetchall()
        timeseries_dict = {q['nucid']:np.zeros(self.duration) for q in uniq_}

        for row in q:
            timeseries_dict[row['nucid']][row['time']] = row['sum(quantity*massfrac)']
        keys = sorted(timeseries_dict.keys(), key=lambda i:sum(timeseries_dict[i]), reverse=True)[:n_isos]
        x = np.arange(self.duration)
        return x, {self.nucid_convert(k):v for k,v in timeseries_dict.items() if k in keys}



    def agent_deployment_window(self):
        """
        plots / exports prototype entry and exit
        """
        self.guide("""
            Facility Prototype Deployment:
            
            You can plot / export different facility prototype deployment:
            
            1. [enter]: number of facilities entered (commissioned) at each timestep
            2. [exit]: number of facilities exited (decommissioned) at each timestep
            3. [deployed]: number of facilities `at play' at each timestep""")

        self.agent_dep_window = Toplevel(self.master)
        self.agent_dep_window.title('Facility Prototype Deployment / Exit Window')
        self.agent_dep_window.geometry('+%s+%s' %(int(self.screen_width/4), int(self.screen_height/2)))
        parent = self.agent_dep_window
        # s = bwidget.ScrolledWindow(self.agent_dep_window, auto='vertical', scrollbar='vertical')
        # f = bwidget.ScrollableFrame(s, constrainedwidth=True)
        # g = f.getframe()

        entry = self.cur.execute('SELECT DISTINCT prototype FROM agententry WHERE kind="Facility"').fetchall()
        proto_list = [i['prototype'] for i in entry]
        proto_list.sort(key=str.lower)
        parent = assess_scroll_deny(len(entry), self.agent_dep_window)
        if parent == -1:
            return

        columnspan = 7


        Label(parent, text='List of Agents', bg='yellow').grid(row=0, columnspan=columnspan)
        Label(parent, text='======================').grid(row=1, columnspan=columnspan)
        Label(parent, text='=====Plot=====', bg='pale green').grid(row=2, columnspan=3)
        Label(parent, text='=====Export=====', bg='SkyBlue1').grid(row=2, column=4, columnspan=3)
        row = 3
        for i in proto_list:
            Label(parent, text=i, bg='light salmon').grid(row=row, column=3)
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
            self.plot(x, y, 'Number of %s (%s)' %(prototype, which), '%s_%s' %(prototype, which))
        elif action == 'export':
            self.export(x, y, '%s_%s.csv' %(prototype, which))


    def timeseries_window(self):
        self.guide("""
            Timeseries
            
            Cyclus has a useful tool of `timeseries', where
            any agent can `report' to the timeseries,
            and any agent can `listen' to the timeseries.
            
            This is to record significant data (e.g. operating
            history, inventory etc.) or communicate to other
            agents (e.g. commodity demand / supply). Here you
            can plot / export the different timeseries
            that were written in the simulation.
            """)
        self.ts_window = Toplevel(self.master)
        self.ts_window.title('Timeseries Window')
        self.ts_window.geometry('+%s+%s' %(int(self.screen_width/4), int(self.screen_height/2)))
        parent = self.ts_window

        tables = self.cur.execute('SELECT name FROM sqlite_master WHERE type="table"').fetchall()
        timeseries_tables_list = []
        for i in tables:
            if 'TimeSeries' in i['name']:
                timeseries_tables_list.append(i['name'].replace('TimeSeries', ''))
        timeseries_tables_list.sort()
        parent = assess_scroll_deny(len(timeseries_tables_list), self.ts_window)
        if parent == -1:
            return

        columnspan = 2
        Label(parent, text='List of Timeseries', bg='yellow').grid(row=0, columnspan=columnspan)
        Label(parent, text='======================').grid(row=1, columns=columnspan)
        row = 2

        for i in timeseries_tables_list:
            Label(parent, text=i, bg='pale green').grid(row=row, column=0)
            Button(parent, text='more', command=lambda timeseries=i: self.timeseries_action(timeseries)).grid(row=row, column=1)
            row += 1

    def timeseries_action(self, timeseries):
        agentid_list_q = self.cur.execute('SELECT distinct agentid FROM TimeSeries%s' %timeseries).fetchall()
        agentid_list = [i['agentid'] for i in agentid_list_q]
        agentname_list = [self.id_proto_dict[i] for i in agentid_list]
        self.ta_window = Toplevel(self.ts_window)
        self.ta_window.title('%s Timeseries Window' %timeseries.capitalize())
        self.ta_window.geometry('+%s+%s' %(int(self.screen_width/3), int(self.screen_height/2)))
        parent = self.ta_window

        parent = assess_scroll_deny(len(agentname_list), self.ta_window)
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


        if agentid == 'agg':
            name = '%s_aggregate_timeseries.csv' % timeseries
        else:
            name = '%s_%s_timeseries.csv' %(self.id_proto_dict[agentid], timeseries)

        if action == 'plot':
            self.plot(x, y, '%s Timeseries' %timeseries, name.replace('.csv', ''))
        elif action == 'export':
            self.export(x, y, name)


    def facility_inventory_window(self):
        # check if explicit inventory is okay

        isit = self.cur.execute('SELECT * FROM InfoExplicitInv').fetchone()
        if not isit['RecordInventory']:
            messagebox.showerror('Dont have it', 'This simulation was run without `explicit_inventory` turned on in the simulation definition. Turn that on and run the simulation again to view the inventory.')
            return

        self.guide("""
            Inventory
            
            If you have `explicit_inventory' on when running the
            simulation, you can plot / export the inventory of each
            facility agent at each timestep. 

            agent: For each unique agent(id), its explicit inventory
                     timeseries is exported / plotted.
            prototype: For each unique prototype (agents with same 
                        prototype name is aggregated), the explicit
                        inventory timeseries is exported / plotted.
            """)
        # show material trade between prototypes
        self.inv_window = Toplevel(self.master)
        self.inv_window.title('Which Selection')
        self.inv_window.geometry('+%s+%s' %(int(self.screen_width/99999), int(self.screen_height/2)))

        parent = self.inv_window
        Label(parent, text='Group by agent or prototype:', bg='yellow').pack()
        Button(parent, text='Group by agent', command=lambda: self.inv_inv_window(groupby='agent')).pack()
        Button(parent, text='Group by prototype', command=lambda: self.inv_inv_window(groupby='prototype')).pack()

    def inv_inv_window(self, groupby):

        # show material trade between prototypes
        self.inv_inv_window_ = Toplevel(self.inv_window)
        self.inv_inv_window_.title('Groupby %s' %groupby)
        self.inv_inv_window_.geometry('+%s+%s' %(int(self.screen_width/1.5), int(self.screen_height/1.5)))

        parent = self.inv_inv_window_
        if groupby == 'agent':
            parent = assess_scroll_deny(len(self.id_proto_dict.keys()), self.inv_inv_window_)
            if parent == -1:
                return

            # show the list of all agents to display
            columnspan = 3
            Label(parent, text='List of Agents', bg='yellow').grid(row=0, columnspan=columnspan)
            Label(parent, text='Agent (id)', bg='pale green').grid(row=1, column=0)
            Label(parent, text='======================').grid(row=2, columnspan=columnspan)
            row = 3
            for id_, proto_ in self.id_proto_dict.items():
                Label(parent, text= '%s (%s)' %(proto_, id_), bg='pale green').grid(row=row, column=0)
                Button(parent, text='plot', command=lambda id_list=[id_]: self.inv_action(id_list, 'plot')).grid(row=row, column=1)
                Button(parent, text='export', command=lambda id_list=[id_]: self.inv_action(id_list, 'export')).grid(row=row, column=2)
                row += 1 
        
        elif groupby == 'prototype':
            # show the list of prototypes to display
            entry = self.cur.execute('SELECT DISTINCT prototype FROM agententry WHERE kind="Facility"').fetchall()
            proto_list = [i['prototype'] for i in entry]
            proto_list.sort(key=str.lower)

            parent = assess_scroll_deny(len(self.id_proto_dict.keys()), self.inv_inv_window_)
            if parent == -1:
                return
            columnspan=3
            Label(parent, text='List of Prototypes', bg='yellow').grid(row=0, columnspan=columnspan)
            Label(parent, text='Prototype Name', bg='pale green').grid(row=1, column=0)
            Label(parent, text='======================').grid(row=2, columnspan=columnspan)
            

            row = 3
            for i in proto_list:
                id_list = [k for k,v in self.id_proto_dict.items() if v == i]
                Label(parent, text= '%s' %i, bg='pale green').grid(row=row, column=0)
                Button(parent, text='plot', command=lambda id_list=id_list: self.inv_action(id_list, 'plot')).grid(row=row, column=1)
                Button(parent, text='export', command=lambda id_list=id_list: self.inv_action(id_list, 'export')).grid(row=row, column=2)
                row += 1


    def inv_action(self, id_list, action):
        n_isos = self.check_n_isos()
        if n_isos == -1:
            return
        str_id_list = [str(q) for q in id_list]
        if n_isos == 0:
            query = 'SELECT sum(quantity), time FROM ExplicitInventory WHERE (agentid = ' + ' OR agentid = '.join(str_id_list) + ') GROUP BY time'
            q = self.cur.execute(query).fetchall()
            x, y = self.query_result_to_timeseries(q, 'sum(quantity)')
        else:
            query = 'SELECT sum(quantity), nucid, time FROM ExplicitInventory WHERE (agentid = ' + ' OR agentid = '.join(str_id_list) + ') GROUP BY time, nucid'
            q = self.cur.execute(query).fetchall()
            x, y = self.query_result_to_timeseries(q, 'nucid', 'sum(quantity)')
        name = self.id_proto_dict[id_list[0]]
        if action == 'plot':
            self.plot(x, y, '%s Inventory' %name, '%s_inv' %name)
        elif action == 'export':
            self.export(x, y, '%s_inv.csv' %name)


    def plot_flow(self):
        transactions = self.cur.execute('SELECT * FROM transactions').fetchall()
        agentids = self.cur.execute('SELECT * FROM agententry').fetchall()

        ids = [q['agentid'] for q in agentids]
        ps = [q['prototype'] for q in agentids]
        id_dict = {k:v for k,v in zip(ids, ps)}

        transaction_columns = [w['name'] for w in self.cur.execute('pragma table_info(transactions)').fetchall()]
        # make transactions table to pandas dataframe for easier parsing
        df = pd.DataFrame(transactions)
        df.columns = transaction_columns
        df['receiver']  = [id_dict[q] for q in df['ReceiverId']]
        df['sender'] = [id_dict[q] for q in df['SenderId']]

        only_sender = []
        s = list(set(df['sender']))
        r = list(set(df['receiver']))
        for i in s:
            if i not in r and i not in only_sender:
                only_sender.append(i)
        flow = [only_sender]
        cache = []
        while True:
            commods = list(set(df[df['sender'].isin(flow[-1])]['Commodity']))
            if commods == []:
                break
            d = {}
            rs = []
            for commod in commods:
                d[commod] = list(set(df[df['Commodity'] == commod]['receiver']))
                rs.extend(d[commod])
            if (all(x in cache for x in rs)):
                break
            rs = [x for x in rs if x not in cache]
            cache.extend(rs)
            flow.append(rs)

        already = []
        flow_clean = []
        for i in flow:
            i = [q for q in i if q not in already]
            already.extend(i)
            flow_clean.append(i)
        flow_clean = [q for q in flow_clean if len(q) != 0]


        max_col = max([len(q) for q in flow_clean])
        maxx = 5 * max_col
        maxy = 14 * len(flow_clean)
        y_coords = np.linspace(0, maxx, len(flow_clean))[::-1]
        x_coords = np.linspace(0, maxy, max([len(q) for q in flow_clean]))
        # xgap = x_coords[1] - x_coords[0]
        ygap = y_coords[1] - y_coords[0]

        uniq_commods = list(set(df['Commodity']))
        commod_color_dict = {k:v for k,v in zip(uniq_commods, np.linspace(0, 1, len(uniq_commods)))}
        uniq_arches_query = self.cur.execute('SELECT * FROM Agententry WHERE Kind=="Facility"').fetchall()
        uniq_arches = list(set(q['Spec'] for q in uniq_arches_query))
        protos = list(set([q['Prototype'] for q in uniq_arches_query]))
        arche_color = {k:v for k,v in zip(uniq_arches, np.linspace(0,1,len(uniq_arches)))}
        proto_arche_dict = {k:v for k,v in zip([q['Prototype'] for q in uniq_arches_query], [q['Spec'] for q in uniq_arches_query])}
        proto_color_dict = {proto:arche_color[proto_arche_dict[proto]] for proto in protos}


        stairs = 10
        steps = list(np.linspace(-1.0 * ygap / 2, ygap / 2, stairs))
        # repeat it. quite hacky
        steps = steps * (int(max_col / len(steps)) + 1)

        # actually building 
        colormap = 'tab20'
        plt.rcParams['image.cmap'] = colormap
        plt.figure(figsize=(5 * len(flow_clean), 0.5*max_col))
        G = nx.DiGraph()
        
        for indx, val in enumerate(flow_clean):
            n = len(val)
            if not n == len(x_coords):
                new_x_coords = x_coords[::int(len(x_coords)/(n+1))][1:]
                grad = False
            else:
                val = val[::-1]
                new_x_coords = x_coords
                grad = True
            for indx2, val2 in enumerate(val):
                if grad:
                    p = steps[indx2]
                else:
                    p = 0
                G.add_node(val2, pos=(new_x_coords[indx2], y_coords[indx]+p), color=proto_color_dict[val2])

        pos = nx.get_node_attributes(G, 'pos')

        trades = df.drop_duplicates(subset=['sender', 'receiver'])
        for indx, row in trades.iterrows():
            G.add_edge(row['sender'], row['receiver'], color=matplotlib.cm.get_cmap(colormap)(commod_color_dict[row['Commodity']]))

        edges = G.edges()
        edge_colors = [G[u][v]['color'] for u, v in edges]
        nodes = G.nodes()
        node_colors = list(nx.get_node_attributes(G, 'color').values())

        # this is for legend
        f = plt.figure(1)
        ax = f.add_subplot(1,1,1)
        for key, val in arche_color.items():
            ax.scatter([0],[0], c=[matplotlib.cm.get_cmap(colormap)(val)], label=key)
        for key, val in commod_color_dict.items():
            ax.plot([0],[0], color=matplotlib.cm.get_cmap(colormap)(val), label=key)

        nx.draw(G, pos, with_labels=True, edge_color=edge_colors, node_color=node_colors, ax=ax)
        plt.text(0.5, 0, '*Only one node per unique prototype name is shown.', fontdict={'color':'red'})
        plt.legend(loc='lower right', fancybox=True, framealpha=0.5, ncol=2)
        plt.show()


    ############################################################
    ############################################################
    ############################################################
    # helper functions

    def plot(self, x, y, ylabel, title='', xlabel='Date'):
        if self.config_dict['cumulative'].get() == 'True':
            if type(y) is dict:
                new_y = {k: np.cumsum(v) for k, v in y.items()}
                y = new_y
            else:
                y = np.cumsum(y)
        fig = plt.figure()
        ax1 = fig.add_subplot(111)
        ax2 = ax1.twiny()
        lines = []
        if type(y) is dict:
            for key, val in y.items():
                l, = ax1.plot(self.timestep_to_date(x), val, label=key)
                lines.append(l)
            if sum([sum(y[k]) for k in y]) > 1e3:
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
        ax2.set_xticklabels(l)
        ax2.set_xlabel('Timesteps')
        ax1.legend(handles=lines)
        plt.yscale(self.config_dict['y_scale'].get())
        plt.ylabel(ylabel)
        title = title + '_' + self.config_dict['suffix'].get()
        plt.title(title.replace('_', ' '))
        plt.grid()
        plt.tight_layout()
        plt.show()


    def nucid_convert(self, nucid):
        e = int(nucid) // 10000
        a = e % 1000
        z = e // 1000
        name = self.z_el_dict[z]
        if self.config_dict['nuc_notation'].get() == 'ZZAAA':
            return str(z) + str(a)
        else:
            return name + str(a)



    def export(self, x, y, filename):
        if self.config_dict['cumulative'].get() == 'True':
            if type(y) is dict:
                new_y = {k: np.cumsum(v) for k, v in y.items()}
                y = new_y
            else:
                y = np.cumsum(y)
        indx = filename.index('.')
        filename = filename[:indx] + '_' + self.config_dict['suffix'].get() + filename[indx:]
        export_dir = os.path.join(self.output_path, 'exported_csv')
        if not os.path.exists(export_dir):
            os.mkdir(export_dir)
        filename = os.path.join(export_dir, filename)
        if type(y) is dict:
            columns = [str(q) for q in list(y.keys())]
            s = 'time, %s\n' %', '.join(columns)
            for indx, val in enumerate(x):
                s += '%s, %s\n' %(str(x[indx]), ', '.join([str(q[indx]) for q in list(y.values())]))
        else:
            s = 'time, quantity\n'
            for indx, val in enumerate(x):
                s += '%s, %s\n' %(str(x[indx]), str(y[indx]))
        with open(filename, 'w') as f:
            f.write(s)
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
                             time_col_name='time'):
        x = np.arange(self.duration)
        y = {}
        keys = list(set([q[vary_col_name] for q in query_result]))
        for i in keys:
            y[i] = np.zeros(self.duration)
        for i in query_result:
            y[i[vary_col_name]] += i[val_col]
        y1 = {k:np.mean(v) for k, v in y.items()}
        n = int(self.config_dict['n_isos'].get())
        keys = sorted(y1, key=y1.__getitem__, reverse=True)[:n]
        new_y = {k:v for k, v in y.items() if k in keys}
        return x, new_y


    def aggregate_dates(self, x, y, agg_dt):
        # roughly aggregates
        groups = int(self.agg_dt / self.dt)
        new_x = np.arange(self.duration / groups)
        new_y = []


    def check_n_isos(self):
        n_isos = self.config_dict['n_isos'].get()
        if n_isos == '':
            return 0
        try:
            print(n_isos)
            return(int(n_isos))
        except:
            messagebox.showerror('You put in %s for the number of isotopes\n It should be an integer' %n_isos)
            return -1

    def metaguide(self):
        self.metaguide_window = Toplevel(self.master)
        self.metaguide_window.title('Backend Analysis Guide')
        self.metaguide_window.geometry('+%s+0' %(int(self.screen_width/1.5)))
        txt = """
        Here you can perform backend analysis of the Cyclus run.

        For more advanced users, you can navigate the tables yourself,
        using a sql query.

        For more beginner-level users, you can use the get material
        flow to obtain material flow, composition, etc for between
        facilities.

        The configure window has variables you can set for plot/export
        settings. If you leave `plot top n isos' blank, it will plot/export
        the total mass flow.

        """
        self.metaguide_text = StringVar()
        self.metaguide_text.set(txt)

        Label(self.metaguide_window, textvariable=self.metaguide_text, justify=LEFT).pack(padx=30, pady=30)

    def guide(self, txt=''):
        try:
            self.guide_window.destroy()
        except:
            z = 0
        self.guide_window = Toplevel(self.master)
        self.guide_window.title('Backend Analysis Guide')
        self.guide_window.geometry('+%s+%s' %(int(self.screen_width/1.5), int(self.screen_height/2)))
        if txt == '':
            txt = """
            Here you can perform backend analysis of the Cyclus run.

            For more advanced users, you can navigate the tables yourself,
            using a sql query.

            For more beginner-level users, you can use the get material
            flow to obtain material flow, composition, etc for between
            facilities.

            The configure window has variables you can set for plot/export
            settings. If you leave `plot top n isos' blank, it will plot/export
            the total mass flow.

            """
        self.guide_text = StringVar()
        self.guide_text.set(txt)

        Label(self.guide_window, textvariable=self.guide_text, justify=LEFT).pack(padx=30, pady=30)
