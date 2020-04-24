import numpy as np
import os
import shutil
import json
import copy
import sqlite3 as lite
from argparse import ArgumentParser, FileType, Namespace, SUPPRESS
import sys
here = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.join(here, os.pardir, 'util'))
from processor import load_environment, BinnedData, Sheet, Options, Processor



class CyclusPostrunner:
    def __init__(self, sqlite_path):
        #!
        self.get_cursor(sqlite_path)
        self.get_times()
        self.get_id_proto_dict()
        self.el_z_dict = {'H': 1, 'He': 2, 'Li': 3, 'Be': 4, 'B': 5, 'C': 6, 'N': 7, 'O': 8, 'F': 9, 'Ne': 10, 'Na': 11, 'Mg': 12, 'Al': 13, 'Si': 14, 'P': 15, 'S': 16, 'Cl': 17, 'Ar': 18, 'K': 19, 'Ca': 20, 'Sc': 21, 'Ti': 22, 'V': 23, 'Cr': 24, 'Mn': 25, 'Fe': 26, 'Co': 27, 'Ni': 28, 'Cu': 29, 'Zn': 30, 'Ga': 31, 'Ge': 32, 'As': 33, 'Se': 34, 'Br': 35, 'Kr': 36, 'Rb': 37, 'Sr': 38, 'Y': 39, 'Zr': 40, 'Nb': 41, 'Mo': 42, 'Tc': 43, 'Ru': 44, 'Rh': 45, 'Pd': 46, 'Ag': 47, 'Cd': 48, 'In': 49, 'Sn': 50, 'Sb': 51, 'Te': 52, 'I': 53, 'Xe': 54, 'Cs': 55, 'Ba': 56, 'La': 57, 'Ce': 58, 'Pr': 59, 'Nd': 60, 'Pm': 61, 'Sm': 62, 'Eu': 63, 'Gd': 64, 'Tb': 65, 'Dy': 66, 'Ho': 67, 'Er': 68, 'Tm': 69, 'Yb': 70, 'Lu': 71, 'Hf': 72, 'Ta': 73, 'W': 74, 'Re': 75, 'Os': 76, 'Ir': 77, 'Pt': 78, 'Au': 79, 'Hg': 80, 'Tl': 81, 'Pb': 82, 'Bi': 83, 'Po': 84, 'At': 85, 'Rn': 86, 'Fr': 87, 'Ra': 88, 'Ac': 89, 'Th': 90, 'Pa': 91, 'U': 92, 'Np': 93, 'Pu': 94, 'Am': 95, 'Cm': 96, 'Bk': 97, 'Cf': 98, 'Es': 99, 'Fm': 100, 'Md': 101, 'No': 102, 'Lr': 103}
        self.z_el_dict = {v:k for k, v in self.el_z_dict.items()}
        self.csv_string = 'CYCLUS\n'
        self.generate_trade_flow('prototype')
        self.generate_trade_flow('agent')
        self.generate_commodity_flow()
        self.generate_agent_flow()

        with open(sqlite_path.replace('.sqlite', '.csv'), 'w') as f:
            f.write(self.csv_string)

    ###########################
    # Auxiliary functions
    ###########################
    def nucid_convert(self, nucid):
        e = int(nucid) // 10000
        a = e % 1000
        z = e // 1000
        name = self.z_el_dict[z]
        if self.config_dict['nuc_notation'].get() == 'ZZAAA':
            return str(z) + str(a)
        else:
            return name + str(a)


    def timestep_to_date(self, timestep):
        timestep = np.array(timestep) 
        month = self.init_month + (timestep * (self.dt / 2629846))
        year = self.init_year + month//12
        month = month%12
        dates = [x+(y/12) for x, y in zip(year, month)]
        return dates


    def get_cursor(self, sqlite_path):
        con = lite.connect(sqlite_path)
        con.row_factory = lite.Row
        self.cur = con.cursor()


    def get_times(self):
        i = self.cur.execute('SELECT * FROM info').fetchone()
        self.init_year = i['InitialYear']
        self.init_month = i['InitialMonth']
        self.duration = i['Duration']
        i = self.cur.execute('SELECT * FROM TimeStepDur').fetchone()
        self.dt = i['DurationSecs']


    def get_id_proto_dict(self):
        # returns dictionary of key 
        agentids = self.cur.execute('SELECT agentid, prototype, kind FROM agententry').fetchall()
        self.id_proto_dict = {agent['agentid']:agent['prototype'] for agent in agentids if agent['kind']=='Facility'}



    def get_iso_flow_dict(self, where_phrase, n_isos, time_col_name='Time'):
        q = self.cur.execute('SELECT time, quantity, resources.qualid, nucid, sum(quantity*massfrac) FROM transactions INNER JOIN resources ON transactions.resourceid = resources.resourceid INNER JOIN compositions on compositions.qualid = resources.qualid WHERE %s GROUP BY nucid, time' %where_phrase).fetchall()
        uniq_ = self.cur.execute('SELECT DISTINCT(nucid) FROM transactions INNER JOIN resources ON resources.resourceid = transactions.resourceid INNER JOIN compositions ON compositions.qualid = resources.qualid WHERE %s' %where_phrase).fetchall()
        timeseries_dict = {q['nucid']:np.zeros(self.duration) for q in uniq_}

        for row in q:
            timeseries_dict[row['nucid']][row['time']] = row['sum(quantity*massfrac)']
        keys = sorted(timeseries_dict.keys(), key=lambda i:sum(timeseries_dict[i]), reverse=True)[:n_isos]
        x = np.arange(self.duration)
        return x, {self.nucid_convert(k):v for k,v in timeseries_dict.items() if k in keys}


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


    ###########################
    ###########################
    # Generation functions
    ###########################


    def generate_trade_flow(self, groupby):
        traders = self.cur.execute('SELECT DISTINCT senderid, receiverid, commodity FROM transactions').fetchall()
        table_dict = {'sender':[], 'receiver': [], 'commodity': []}
        if groupby == 'agent':
            table_dict['sender'] = [self.id_proto_dict[i['senderid']] + '(%s)' %str(i['senderid']) for i in traders]
            table_dict['receiver'] = [self.id_proto_dict[i['receiverid']] + '(%s)' %str(i['receiverid']) for i in traders]
            table_dict['commodity'] = [i['commodity'] for i in traders]
        elif groupby == 'prototype':
            already = []
            for i in traders:
                checker = [self.id_proto_dict[i['senderid']], self.id_proto_dict[i['receiverid']], i['commodity']]
                if checker in already:
                    continue
                else:
                    already.append(checker)
                    table_dict['sender'].append(checker[0])
                    table_dict['receiver'].append(checker[1])
                    table_dict['commodity'].append(checker[2])
        
        # should generate a csv with all possible combinations?
        # format is the following:
        # first row: keyword
        # second row: x values (space separated)
        # sender, receiver, commodity, y (space separated)
        self.csv_string += 'BEGIN trade_flow_%s' %groupby + '\n'
        for indx, val in enumerate(table_dict['sender']):
            s, r, c = table_dict['sender'][indx], table_dict['receiver'][indx], table_dict['commodity'][indx]
            x, y = self.get_trade_flow(s, r, c, groupby=groupby)
            if indx != 0:
                if (prev_x != x).all():
                    raise ValueError('The x values are not the same!')
            else:
                self.csv_string += ','.join([str(q) for q in x]) + '\n'

            if groupby == 'prototype':
                self.csv_string  += '%s -> [%s] -> %s' %(s,c,r) + ',' + ','.join([str(q) for q in y]) + '\n'
            else: #groupby == 'agent'
                sender_name = s[:s.index('(')]
                receiver_name = r[:r.index('(')]
                sender_id = s[s.index('(')+1:s.index(')')]
                receiver_id = r[r.index('(')+1:r.index(')')]
                label = '%s (%s) -> [%s] -> %s (%s)' %(sender_name, sender_id, c, receiver_name, receiver_id)
                self.csv_string += label + ',' + ','.join([str(q) for q in y]) + '\n'

            prev_x = x

        self.csv_string += 'END trade_flow_%s\n' %groupby


    def generate_commodity_flow(self):
        commods = self.cur.execute('SELECT DISTINCT commodity FROM transactions').fetchall()
        self.csv_string += 'BEGIN commodity_flow\n'
        for indx, i in enumerate(commods):
            commod = i['commodity']
            x, y = self.get_commodity_flow(commod)
            if indx != 0:
                if (prev_x != x).all():
                    raise ValueError('The x values are not the same')
            else:
                self.csv_string += ','.join([str(q) for q in x]) + '\n'

            self.csv_string += commod + ',' + ','.join([str(q) for q in y])+'\n'
            prev_x = x

        self.csv_string += 'END commodity_flow\n'


    def generate_agent_flow(self):
        entry = self.cur.execute('SELECT DISTINCT prototype FROM agententry WHERE kind="Facility"').fetchall()
        for which in ['entered', 'exited', 'deployed']:
            self.csv_string += 'BEGIN agent_flow_%s\n' %which
            for indx, i in enumerate(entry):
                proto = i['prototype']
                x, y = self.get_agent_flow(proto, which)
                if indx != 0:
                    if (prev_x != x).all():
                        raise ValueError('The x values are not the same')
                else:
                    self.csv_string += ','.join([str(q) for q in x]) + '\n'

                self.csv_string += proto + ',' + ','.join([str(q) for q in y]) + '\n'
                prev_x = x
            
            self.csv_string += 'END agent_flow_%s\n' %which



    def generate_timeseries_flow(self):
        tables = self.cur.execute('SELECT name FROM sqlite_master WHERE type="table"').fetchall()
        timeseries_tables_list = [i['name'].replace('TimeSeries', '') for i in tables if 'TimeSeries' in i['name']]
        timeseries_tables_list.sort()

        for timeseries in timeseries_tables_list:
            z=0


    def generate_inventory_flow(self, groupby):
        isit = self.cur.execute('SELECT * FROM InfoExplicitInv').fetchone()
        if not isit['RecordInventory']:
            raise ValueError('This simulation was run without `explicit_inventory` turned on.')

        if groupby == 'agent':
            # get list of agents
            self.id_proto_dict

        else:
            # et list of prototypes
            entry = self.cur.execute('SELECT DISTINCT prototype FROM agententry WHERE kind="Facility"').fetchall()
            proto_list = [i['prototype'] for i in entry]
            proto_list.sort(key=str.lower)



    

    ###########################
    ###########################
    # Generation functions
    ###########################

    def get_trade_flow(self, sender, receiver, commodity, groupby):
        n_isos = 0 

        if groupby == 'prototype':
            receiver_id = [k for k,v in self.id_proto_dict.items() if v == receiver]
            sender_id = [k for k,v in self.id_proto_dict.items() if v == sender]
        else:
            sender_name = sender[:sender.index('(')]
            receiver_name = receiver[:receiver.index('(')]
            sender_id = [sender[sender.index('(')+1:sender.index(')')]]
            receiver_id = [receiver[receiver.index('(')+1:receiver.index(')')]]

        str_sender_id = [str(q) for q in sender_id]
        str_receiver_id = [str(q) for q in receiver_id]
        if n_isos == 0:
            query = 'SELECT sum(quantity), time FROM transactions INNER JOIN resources ON transactions.resourceid == resources.resourceid WHERE (senderid = ' + ' OR senderid = '.join(str_sender_id) + ') AND (receiverid = ' + ' OR receiverid = '.join(str_receiver_id) + ') GROUP BY time'
            q = self.cur.execute(query).fetchall()
            x, y = self.query_result_to_timeseries(q, 'sum(quantity)')
        else:
            x, y = self.get_iso_flow_dict('(senderid = ' + ' OR senderid = '.join(str_sender_id) + ') AND (receiverid = ' + ' OR receiverid = '.join(str_receiver_id) + ')', n_isos)

        return x, y
        

    def get_commodity_flow(self, commod):
        n_isos = 0
        if n_isos == 0:
            movement = self.cur.execute('SELECT time, sum(quantity) FROM transactions INNER JOIN resources on transactions.resourceid==resources.resourceid WHERE commodity="%s" GROUP BY time' %commod).fetchall()
            x, y = self.query_result_to_timeseries(movement, 'sum(quantity)')
        else:
            x, y = self.get_iso_flow_dict('commodity = "%s"' %commod, n_isos)
        return x, y


    def get_agent_flow(self, prototype, which):
        entry = self.cur.execute('SELECT agentid, entertime FROM agententry WHERE prototype="%s"' %prototype).fetchall()
        agent_id_list = [i['agentid'] for i in entry]
        entertime = [i['entertime'] for i in entry]
        exittime = []
        for i in agent_id_list:
            try:
                exit = self.cur.execute('SELECT agentid, exittime FROM agentexit WHERE agentid=%s' %str(i)).fetchone()
            except:
                continue
            if exit == None:
                exittime.append(-1)
            else:
                exittime.append(exit['exittime'])

        x = np.array(list(range(self.duration)))
        y = []
        if which == 'entered':
            for time in x:
                y.append(entertime.count(time))
        elif which == 'exited':
            for time in x:
                y.append(exittime.count(time))
        elif which == 'deployed':
            deployed = 0
            for time in x:
                deployed += entertime.count(time)
                deployed -= exittime.count(time)
                y.append(deployed)

        return x, y


    def get_timeseries_flow(self, timeseries):
        agentid_list_q = self.cur.execute('SELECT distinct agentid FROM TimeSeries%s' %timeseries).fetchall()
        agentid_list = [i['agentid'] for i in agentid_list_q]
        agentname_list = [self.id_proto_dict[i] for i in agentid_list]


    def get_inventory_flow(self):
        z=0
