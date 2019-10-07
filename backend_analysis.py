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
import analysis as an
import sqlite3 as lite
import numpy as np
import matplotlib.pyplot as plt



class BakendWindow(Frame):
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

        self.guide()
        Label(self.master, text='Choose backend analysis type:').grid(row=0)

        raw_table_button = Button(root, text='View Raw Tables', command=lambda : self.view_raw_tables())
        raw_table_button.pack()

        material_flow_button = Button(root, text='Get Material Flow', command=lambda : self.view_material_flow())
        material_flow_button.pack()


    def get_id_proto_dict(self):
        agentids = self.cur.execute('SELECT agentid, prototype, kind FROM agententry').fetchall()
        self.id_proto_dict = {}
        for agent in agentids:
            if agent['kind'] == 'Facility':
                self.id_proto_dict[agent['agentid']] = agent['prototype']


    def get_cursor(self):
        con = lite.connect(os.path.join(output_path, 'cyclus.sqlite'))
        con.row_factory = lite.Row
        self.cur = con.cursor()


    def view_raw_tables(self):
        self.raw_table_window = Toplevel(self.master)
        self.raw_table_window.title('View Raw Tables')
        self.raw_table_window.geometry('+0+3500')
        # just like a sql query with ability to export and stuff
        self.guide_text = 





    def view_material_flow(self):
        self.guide_text = ''
        # show material trade between facilities



        traders = self.cur.execute('SELECT DISTINCT senderid, receiverid FROM transactions').fetchall()
        # sort by agentid (literally unique agentid)
        uniq_agentid = []
        # sort by prototype name (aggregate same prototypes)
        uniq_prototype = []
        for i in traders:
            one_set = list(i)
            with_agentid = [self.id_proto_dict[x] + '(%s)'%str(x) for x in one_set]
            uniq_agentid.append(with_agentid)
            just_prototype = [self.id_proto_dict[x] for x in one_set]
            uniq_prototype.append(new_set)

        new_uniq_prototype = []
        for i in uniq_prototype:
            if i not in new_uniq_prototype:
                new_uniq_prototype.append(i)

        # just unique prototype and agentid list for income and outgoing material flux
        traders = self.cur.execute('SELECT DISTINCT agentid FROM agententry').fetchall()
        agentids = list(traders)

        traders = self.cur.execute('SELECT DISTINCT prototype FROM agententry').fetchall()
        prototypes = list(traders)




        # create table of sender - receiverid - commodity set like:
        # sender / receiver / begin / end
        # prototype (agentid) / prototype (agentid) / commodity / min(date) / max(date)

        # have an `organize alphabetically / ascending order' for each column



    def plot_material_flow(self, sender_list, receiver_list):
        commodities = self.cur.execute('SELECT DISTINCT commodity FROM transactions WHERE senderid')






    def timestep_to_date(self, timestep):
        startyear = 
        startmonth = 
        startday = 
        dt = 
        if dt != 2629846:
            # change with month / day / week scale?
            # how?
        else:
            month = startmonth + timestep
            year = startyear + month//12
            month = month%12
            return '%s-%s' %(str(year), str(month))


    
    
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
