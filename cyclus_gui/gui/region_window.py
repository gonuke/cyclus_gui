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
from read_xml import *
from window_tools import *

class RegionWindow(Frame):
    def __init__(self, master, output_path):
        """
        Region dict looks like:
        key: region name
        val: dictionary
            key: institution name
            val: array
                [0] prototype name
                [1] n_build
                [2] entertime
                [3] lifetime
        """

        self.master = Toplevel(master)
        self.master.title('Define regions')
        self.output_path = output_path
        self.master.geometry('+150+850')
        self.tot_entry_n = 0
        # self.load_prototypes()
        self.status_var = StringVar()
        self.guide()
        self.region_dict = {}
        self.proto_dict = {}
        try:
            arches, w = read_xml(os.path.join(self.output_path, 'archetypes.xml'), 'arche')
        except:
            arches = []
        self.libs = [x[0] for x in arches]
        Label(self.master, text='Region Name:').grid(row=0, column=0)
        region_name = Entry(self.master)
        region_name.grid(row=0, column=1)
        Button(self.master, text='Add Institution', command=lambda : self.add_inst(region_name.get())).grid(row=1, column=0)
        # I thought I could do d3ploy but it complicates too much.
        # backlog for later maybe
        #if len([q for q in self.libs if 'd3ploy' in q]) != 0:
        #    Button(self.master, text='Add D3ploy Institution', command=lambda : self.add_d3ploy(region_name.get())).grid(row=2, column=0)
        #else:
        #    Label(self.master, text='').grid(row=2, column=0)
        Button(self.master, text='Done', command=lambda : self.done_region()).grid(row=3, column=0)

        if os.path.isfile(os.path.join(self.output_path, 'region.xml')):
            self.region_dict, self.n = read_xml(os.path.join(self.output_path, 'region.xml'),
                                                'region')
        if os.path.isfile(os.path.join(self.output_path, 'facility.xml')):
            self.show_defined_protos()
 
        self.update_status_window()


    def show_defined_protos(self):
        self.proto_dict, arche, n = read_xml(os.path.join(self.output_path, 'facility.xml'),
                              'facility')
        defined_protos_window = Toplevel(self.master)
        defined_protos_window.title('Defined Prototypes')
        defined_protos_window.geometry('+1000+900')
        parent = defined_protos_window
        parent = assess_scroll_deny(n+2, defined_protos_window)
        Label(parent, text='Defined Prototypes', bg='yellow').grid(row=0, column=0)
        Label(parent, text='Archetype', bg='yellow').grid(row=0, column=1)
        row = 1
        for key, val in self.proto_dict.items():
            Label(parent, text=key).grid(row=row, column=0)
            Label(parent, text=arche[key]).grid(row=row, column=1)
            row +=1 

    def update_status_window(self):
        try:
            self.status_window.destroy()
        except:
            z=0
        self.status_window = Toplevel(self.master)
        self.status_window.title('Defined Regions')
        self.status_window.geometry('+500+920')
        parent = self.status_window
        parent = assess_scroll_deny(len(self.proto_dict.keys())+2, self.status_window)
        
        Label(parent, text='Current regions:', bg='yellow').grid(row=0, columnspan=7)
        c_dict = {'Region': 'pale green',
                  'Institution': 'light salmon',
                  'Facility_proto': 'SkyBlue1',
                  'n_build': 'ivory3',
                  'build_time': 'orchid1',
                  'lifetime': 'pale turquoise'}
        columns = ['Region', 'Institution', 'Facility_proto', 'n_build', 'build_time', 'lifetime']
        for indx, val in enumerate(columns):
            c = c_dict[val]
            Label(parent, text=val, bg=c).grid(row=1, column=indx+1)
        row = 2
        for regionname, instdict in self.region_dict.items():
            Button(parent, text='x', command=lambda regionname=regionname: self.del_region(regionname)).grid(row=row, column=0)
            Label(parent, text=regionname, bg='pale green').grid(row=row, column=1)
            row += 1
            for instname, instarray in instdict.items():
                Button(parent, text='x', command=lambda regionname=regionname, instname=instname: self.del_inst(regionname, instname)).grid(row=row, column=0)
                Button(parent, text=instname, command=lambda regionname=regionname, instname=instname: self.update_inst(regionname, instname)).grid(row=row, column=2)
                row += 1
                for instlist in instarray:
                    fac_name = instlist[0]
                    Button(parent, text='x', command=lambda regionname=regionname, instname=instname, fac_name=fac_name: self.del_fac(regionname, instname, fac_name)).grid(row=row, column=0)
                    columns_ = columns[2:]
                    for indx, v in enumerate(instlist):
                        c = c_dict[columns_[indx]]
                        Label(parent, text=v, bg=c).grid(row=row, column=indx+3)
                    row += 1


    def del_region(self, regionname):
        self.region_dict.pop(regionname, None)
        self.update_status_window()       


    def del_inst(self, regionname, instname):
        self.region_dict[regionname].pop(instname, None)
        self.update_status_window()

    def update_inst(self, regionname, instname):
        # open window
        self.add_inst(regionname, instname)

        self.inst_name_entry.insert(END, instname)
        for indx, val in enumerate(self.region_dict[regionname][instname]):
            if indx != 0:
                self.add_inst_row()
            for indx2, val2 in enumerate(self.cat_list):
                self.inst_entry_dict[val2][-1].insert(END, val[indx2])
        

    def del_fac(self, regionname, instname, fac_name):
        for indx, val in enumerate(self.region_dict[regionname][instname]):
            if val[0] == fac_name:
                it = indx
        del self.region_dict[regionname][instname][it]
        self.update_status_window()




        # also get from the prototype file



    def done_region(self):
        if len(self.region_dict) == 0:
            messagebox.showerror('Error', 'No Regions were defined!')
            return
        self.compile_dict_to_xml()
        self.master.destroy()

    def compile_dict_to_xml(self):
        # name, institution
        region_template = '<region>\n\t<name>{name}</name>\n\t<config><NullRegion/></config>\n{institution}\n</region>\n'
        # name, deployinst
        inst_template = '\t<institution>\n\t\t<name>{name}</name>\n\t\t<config>\n\t\t\t<DeployInst>\n{deployinst}\n\t\t\t</DeployInst>\n\t\t</config>\n\t</institution>'
        val_template = '\t\t\t\t\t<val>{entry}</val>\n'
        string = '<root>\n'
        for regionname, inst_dict in self.region_dict.items():
            inst_chunk = ''
            for inst_name, inst_array in inst_dict.items():
                proto_string = '\t\t\t\t<prototypes>\n'
                n_build_string = '\t\t\t\t<n_build>\n'
                buildtime_string = '\t\t\t\t<build_times>\n'
                lifetime_string = '\t\t\t\t<lifetimes>\n'
                for entry in inst_array:
                    proto_string += val_template.format(entry=entry[0])
                    n_build_string += val_template.format(entry=entry[1])
                    buildtime_string += val_template.format(entry=entry[2])
                    lifetime_string += val_template.format(entry=entry[3])
                proto_string += '\t\t\t\t</prototypes>\n'
                n_build_string += '\t\t\t\t</n_build>\n'
                buildtime_string += '\t\t\t\t</build_times>\n'
                lifetime_string += '\t\t\t\t</lifetimes>\n'
                all_four = proto_string + n_build_string + buildtime_string + lifetime_string
                inst_chunk += inst_template.format(name=inst_name, deployinst=all_four)
            string += region_template.format(name=regionname, institution=inst_chunk)
        string += '\n</root>'
        with open(os.path.join(self.output_path, 'region.xml'), 'w') as f:
            f.write(string)
        messagebox.showinfo('Success', 'Successfully rendered %i regions!' %len(self.region_dict))


    def add_inst(self, region_name, instname=''):
        if region_name == '':
            messagebox.showerror('Error', 'You have to define the region name before adding and institution!')
            return
        self.add_inst_window = Toplevel(self.master)
        self.add_inst_window.title('Add institution')
        self.add_inst_window.geometry('+100+1000')
        self.inst_dict = {}
        if instname != '':
            self.add_inst_window = assess_scroll_deny(len(self.region_dict[region_name][instname]),
                                                      self.add_inst_window)

        if region_name not in self.region_dict.keys():
            self.region_dict[region_name] = {}
        self.current_region = region_name
        Label(self.add_inst_window, text='Institution Name:').grid(row=0, column=1)
        self.inst_name_entry = Entry(self.add_inst_window)
        self.inst_name_entry.grid(row=0, column=2)
        Button(self.add_inst_window, text='Done', command= lambda : self.submit_inst(self.inst_name_entry.get())).grid(row=1, column=0)
        Label(self.add_inst_window, text='Add new prototypes here:').grid(row=2, columnspan=3)
        Button(self.add_inst_window, text='Add Row', command= lambda: self.add_inst_row()).grid(row=3, column=3)
        self.inst_entry_dict = {'prototypes': [], 'lifetimes': [],
                                'n_build': [], 'build_times': []}
        self.cat_list = ['prototypes', 'n_build', 'build_times', 'lifetimes']
        for indx, val in enumerate(self.cat_list):
            Label(self.add_inst_window, text=val).grid(row=4, column=indx)
            self.inst_entry_dict[val].append(Entry(self.add_inst_window))
            self.inst_entry_dict[val][-1].grid(row=5, column=indx)
        self.rownum = 6

        # show realtime institutions added

    def add_d3ploy(self, region_name, instname=''):
        if region_name == '':
            messagebox.showerror('Error', 'You have to define the region name before adding and institution!')
            return
        self.add_d3ploy_window = Toplevel(self.master)
        self.add_d3ploy_window.title('Add D3ploy Institution')
        self.add_d3ploy_window.geometry('+100+1000')
        self.d3ploy_dict = {}
        if instname != '':
            self.add_d3ploy_window = assess_scroll_deny(len(self.d3ploy_dict.keys()),
                                                        self.add_d3ploy_window)
        if region_name not in self.region_dict.keys():
            self.region_dict[region_name] = {}
        self.current_region = region_name
        self.d3ploy_entry_dict = {}
        
        cat = ['institution_name', 'driving_commodity', 'demand_equation',
               'prediction_method', 'regression_backsteps']
        for indx, val in enumerate(cat):
            disp_name = val.replace('_', ' ').capitalize() + ':'
            Label(self.add_d3ploy_window, text=disp_name).grid(row=indx, column=1)
            self.d3ploy_entry_dict[val] = Entry(self.add_d3ploy_window)
            self.d3ploy_entry_dict[val].grid(row=indx, column=2)
        self.rownum = indx + 1
        Button(self.add_d3ploy_window, text='Done', command=lambda : self.submit_d3ploy(self.d3ploy_entry_dict['institution_name'].get())).grid(row=0, column=0)
        Button(self.add_d3ploy_window, text='Add Row', command= lambda: self.add_d3ploy_row()).grid(row=1, column=0)

        Label(self.add_d3ploy_window, text=' ').grid(row=self.rownum, columnspan=3)
        self.rownum += 1
        self.d3ploy_entry_dict = {}
        # d3ploy_entry_dict:
        #   key: category
        #   val: list of entries for values
        self.d3ploy_cat = ['facility_name', 'commodity', 'capacity', 'preference', 'constraintcommod', 'constraintval']
        if_optional = [0, 0, 0, 1, 1, 1]
        for indx, val in enumerate(self.d3ploy_cat):
            color = 'snow'
            if if_optional[indx]:
                color='salmon1'
            Label(self.add_d3ploy_window, text=val, bg=color).grid(row=self.rownum, column=indx)
            # initialize list for filling it up
            self.d3ploy_entry_dict[val] = []
            self.d3ploy_entry_dict[val].append(Entry(self.add_d3ploy_window))
            self.d3ploy_entry_dict[val][-1].grid(row=self.rownum+1, column=indx)
        self.rownum += 1

    def add_d3ploy_row(self):
        for indx, val in enumerate(self.d3ploy_cat):
            self.d3ploy_entry_dict[val].append(Entry(self.add_d3ploy_window))
            self.d3ploy_entry_dict[val][-1].grid(row=self.rownum, column=indx)
        self.rownum += 1


    def submit_d3ploy(self, inst_name):
        if inst_name == '':
            messagebox.showerror('Error', 'You have to define an Institution Name')
            return
        d3ploy_array = []
        for indx in range(len(self.d3ploy_entry_dict['facility_name'])):
            # check input validity
            facility_name_ = self.d3ploy_entry_dict['facility_name'][indx].get()
            commodity_ = self.d3ploy_entry_dict['commodity'][indx].get()
            capacity_ = self.d3ploy_entry_dict['capacity'][indx].get()
            preference_ = self.d3ploy_entry_dict['preference'][indx].get()
            constraintcommod_ = self.d3ploy_entry_dict['constraintcommod'][indx].get()
            constraintval_ = self.d3ploy_entry_dict['constraintval'][indx].get()
            if facility_name_ == commodity_ == capacity_ == capacity_ == preference_ == constraintcommod_ == constraintval_ == '':
                continue
            elif '' in [facility_name_, commodity_, capacity_, capacity_,
                        preference_, constraintcommod_, constraintval_]:
                messagebox.showerror('Error', 'You are missing a parameter for line %i' %indx)
                return
            d3ploy_array.append([facility_name_, commodity_, capacity_, capacity_,
                                 preference_, constraintcommod_, constraintval_])

        if len(d3ploy_array) == 0:
            messagebox.showerror('Error', 'There are no entries! ')
            return

        messagebox.showinfo('Added', 'Added institution %s' %inst_name)
        # where to now?
        self.region_dict[self.current_region][inst_name] = 0



            

    def submit_inst(self, inst_name):
        # check input correctness:
        if inst_name == '':
            messagebox.showerror('Error', 'You have to define an Institution Name')
            return
        inst_array = []
        for indx in range(len(self.inst_entry_dict['prototypes'])):
            prototype_ = self.inst_entry_dict['prototypes'][indx].get()
            lifetime_ = self.inst_entry_dict['lifetimes'][indx].get()
            build_time_ = self.inst_entry_dict['build_times'][indx].get()
            n_build_ = self.inst_entry_dict['n_build'][indx].get()
            # skip missing rows
            if prototype_ == lifetime_ == build_time_ == n_build_ == '':
                continue
            # check if there are missing parameters
            elif '' in [prototype_, lifetime_, build_time_, n_build_]:
                messagebox.showerror('Error', 'You are missing a parameter for line %i' %indx)
                return
            # check if the ints are ints
            if not (self.check_if_int(lifetime_) & self.check_if_int(build_time_)
                    & self.check_if_int(n_build_)):
                messagebox.showerror('Error', 'Entertime, lifetime, and n_build have to be integers.')
                return
            inst_array.append([prototype_, n_build_, build_time_, lifetime_])
            
        if len(inst_array) == 0:
            messagebox.showerror('Error', 'There are no entries! ')
            return
        messagebox.showinfo('Added', 'Added institution %s' %inst_name)
        self.region_dict[self.current_region][inst_name] = inst_array
        self.update_status_window()
        self.add_inst_window.destroy()


    def check_if_int(self, string):
        try:
            int(string)
            return True
        except ValueError:
            return False


    def add_inst_row(self):
        for indx, val in enumerate(self.cat_list):
            self.inst_entry_dict[val].append(Entry(self.add_inst_window))
            self.inst_entry_dict[val][-1].grid(row=self.rownum, column=indx)
        self.rownum += 1


    def close_window(self):
        self.master.destroy()

    def guide(self):
        string = """
        This is where you define how the prototypes you defined will be played
        in the simulation - when they enter, how many enters, and when they exit.

        A region has one or many institutions.
        Click on `Add Region', specify a Region Name, and click 'Add Institution'
        to define a single institution. The institution will be part of the region
        you specified.

        One row in the institution definition window is for one prototype.
        Define the name, how many to build, when to enter, and how long to stay
        for each prototype. Click 'Add Row' if you want to add more prototypes.

        Once done, click done to add the institution into the region. The status
        window will reflect the changes you've made.

        A prototype with a `(x)' next to it means that the prototype has not
        been defined by the prototype definition section.

        Once done, click Done in the region window.
        """
        self.guide_window = Toplevel(self.master)
        self.guide_window.title('Region guide')
        self.guide_window.geometry('+0+400')
        Label(self.guide_window, text=string).pack(padx=30, pady=30)

