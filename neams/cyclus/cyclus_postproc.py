import numpy as np
from __future__ import print_function, division
import sys, os
from argparse import ArgumentParser, FileType, Namespace, SUPPRESS
import sqlite3 as lite

class CyclusProcessor(Processor):
    def __init__(self, name='cyclus', options=None):
        super(CyclusProcessor, self).__init__(name, options)
        self.filepath = 'path/to/some/file'
        self.el_z_dict = {'H': 1, 'He': 2, 'Li': 3, 'Be': 4, 'B': 5, 'C': 6, 'N': 7, 'O': 8, 'F': 9, 'Ne': 10, 'Na': 11, 'Mg': 12, 'Al': 13, 'Si': 14, 'P': 15, 'S': 16, 'Cl': 17, 'Ar': 18, 'K': 19, 'Ca': 20, 'Sc': 21, 'Ti': 22, 'V': 23, 'Cr': 24, 'Mn': 25, 'Fe': 26, 'Co': 27, 'Ni': 28, 'Cu': 29, 'Zn': 30, 'Ga': 31, 'Ge': 32, 'As': 33, 'Se': 34, 'Br': 35, 'Kr': 36, 'Rb': 37, 'Sr': 38, 'Y': 39, 'Zr': 40, 'Nb': 41, 'Mo': 42, 'Tc': 43, 'Ru': 44, 'Rh': 45, 'Pd': 46, 'Ag': 47, 'Cd': 48, 'In': 49, 'Sn': 50, 'Sb': 51, 'Te': 52, 'I': 53, 'Xe': 54, 'Cs': 55, 'Ba': 56, 'La': 57, 'Ce': 58, 'Pr': 59, 'Nd': 60, 'Pm': 61, 'Sm': 62, 'Eu': 63, 'Gd': 64, 'Tb': 65, 'Dy': 66, 'Ho': 67, 'Er': 68, 'Tm': 69, 'Yb': 70, 'Lu': 71, 'Hf': 72, 'Ta': 73, 'W': 74, 'Re': 75, 'Os': 76, 'Ir': 77, 'Pt': 78, 'Au': 79, 'Hg': 80, 'Tl': 81, 'Pb': 82, 'Bi': 83, 'Po': 84, 'At': 85, 'Rn': 86, 'Fr': 87, 'Ra': 88, 'Ac': 89, 'Th': 90, 'Pa': 91, 'U': 92, 'Np': 93, 'Pu': 94, 'Am': 95, 'Cm': 96, 'Bk': 97, 'Cf': 98, 'Es': 99, 'Fm': 100, 'Md': 101, 'No': 102, 'Lr': 103}
        self.z_el_dict = {v:k for k, v in self.el_z_dict.items()}
        con = lite.connect(self.filepath)
        con.row_factory = lite.Row
        self.cur = con.cursor()
        self.get_id_proto_dict()
        self.get_start_times()




    ##############################################################################################################################
    ## initializing functions
    def get_id_proto_dict(self):
        agentids = self.cur.execute('SELECT agentid, prototype, kind FROM agententry').fetchall()
        self.id_proto_dict = {}
        for agent in agentids:
            if agent['kind'] == 'Facility':
                self.id_proto_dict[agent['agentid']] = agent['prototype']

    def get_start_times(self):
        i = self.cur.execute('SELECT * FROM info').fetchone()
        self.init_year = i['InitialYear']
        self.init_month = i['InitialMonth']
        self.duration = i['Duration']
        i = self.cur.execute('SELECT * FROM TimeStepDur').fetchone()
        self.dt = i['DurationSecs']


    ##############################################################################################################################

    ##############################################################################################################################
    ## label generation functions
    def generate_material_flow_labels(self, groupby):
        trades = self.cur.execute('SELECT DISTINCT senderid, receiverid, commodity FROM transactions').fetchall()
        if groupby == 'agent':
            table_dict = {'sender': [],
                          'receiver': [],
                           'commodity': []}
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

        #! generate processing son
        #! export_sender_receiver


    def generate_commodity_transfer_labels(self):
        commods = self.cur.execute('SELECT DISTINCT commodity FROM transactions').fetchall()
        names = [i['commodity'] for i in commods]
        names.sort(key=str.lower)
        #! generate processing son
        #export_commodity_transfer


    def generate_agent_deployment_labels(self):
        entry = self.cur.execute('SELECT DISTINCT prototype FROM agententry WHERE kind="Facility"').fetchall()
        proto_list = [i['prototype'] for i in entry]
        proto_list.sort(key=str.lower)
        #! generate processing son
        # export_agent_deployment

    def generate_timeseries_labels(self):
        tables = self.cur.execute('SELECT name FROM sqlite_master WHERE type="table"').fetchall()
        timeseries_table_list = [i['name'].replace('TimeSeries', '') for i in tables if 'TimeSeries' in i]
        timeseries_table_list.sort()
        #! generate processing son
        # export_timeseries


    ##############################################################################################################################


    ##############################################################################################################################
    ## export functions
    def export_sender_receiver(self, sender, receiver, commodity, groupby):
        #! get n_isos from a configuration thing?
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

        self.export_to_csv(x, y,
                           '%s sent' %commodity, '%s->[%s]->%s' %(sender, receiver, commodity))


    def export_commodity_transfer(self, commod):
        movement = self.cur.execute('SELECT time, sum(quantity) FROM transactions INNER JOIN resources ON transactions.resourceid==resources.resourceid WHERE commodity="%s" GROUP BY time' %commod).fetchall()
        x, y = self.query_result_to_timeseries(movement, 'sum(quantity)')

        self.export_to_csv(x, y,
                           '$s sent', commod)

    def export_agent_deployment(self, prototype, which):
        entry = self.cur.execute('SELECT agentid, entertime FROM agententry WHERE prototype="%s"' %prototype).fetchall()
        agent_id_list = [i['agentid'] for i in entry]
        entertime = [i['entertime'] for i in entry]
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

        self.export_to_csv(x, y,
                           'Number of %s (%s)' %(prototype, which), '%s_%s' %(prototype, which))


    def export_timeseries(self, timeseries):
        



    ##############################################################################################################################


    ##############################################################################################################################
    ## helper functions
    def query_result_to_timeseries(self, query_result, col_name,
                                   time_col_name='time'):
        x = np.arange(self.duration)
        y = np.zeros(self.duration)
        for i in query_result:
            y[int(i[time_col_name])] += i[col_name]
        return x, y


    def export_to_csv(x, y, ylabel, title, xlabel='Date'):
        #if self.config_dict['cumulative'].get() == 'True':
        #   if type(y) is dict:
        #       new_y = {k: np.cumsum(v) for k, v in y.items()}
        #       y = new_y
        #   else:
        #       y = np.cumsum(y)
        #! Where to export this to?
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

    ##############################################################################################################################

