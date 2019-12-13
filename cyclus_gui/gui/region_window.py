from tkinter import *
from tkinter import messagebox
from tkinter import filedialog
from tkinter.scrolledtext import ScrolledText
import xmltodict
import uuid
import os
import shutil
import json
import numpy as np
import copy
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from read_xml import *
from window_tools import *
from hovertip import CreateToolTip

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
        try:
            self.duration = int(xmltodict.parse(open(os.path.join(self.output_path, 'control.xml'), 'r').read())['control']['duration'])
        except Exception as e:
            self.duration = 0
        self.proto_dict = {}
        try:
            arches, w = read_xml(os.path.join(self.output_path, 'archetypes.xml'), 'arche')
        except Exception as e:
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
        except Exception as e:
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
                        if indx == 0 and v not in self.proto_dict.keys():
                            v = v + ' (undefined)'
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


    def done_region(self):
        print(self.region_dict)
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
        self.add_inst_window_frame = assess_scroll_deny(100,
                                                  self.add_inst_window)

        if region_name not in self.region_dict.keys():
            self.region_dict[region_name] = {}
        self.current_region = region_name
        Label(self.add_inst_window_frame, text='Institution Name:').grid(row=0, column=1)
        self.inst_name_entry = Entry(self.add_inst_window_frame)
        self.inst_name_entry.grid(row=0, column=2)
        Button(self.add_inst_window_frame, text='Done', command= lambda : self.submit_inst(self.inst_name_entry.get())).grid(row=1, column=0)
        w = Button(self.add_inst_window_frame, text='Power Demand Deploy', command=lambda:self.demand_deploy())
        CreateToolTip(w, text='This allows you to automatically deploy facilities to meet power demand.')
        w.grid(row=1, column=3)
        Label(self.add_inst_window_frame, text='Add new prototypes here:').grid(row=2, columnspan=3)
        Button(self.add_inst_window_frame, text='Add Row', command= lambda: self.add_inst_row()).grid(row=3, column=3)
        self.inst_entry_dict = {'prototypes': [], 'lifetimes': [],
                                'n_build': [], 'build_times': []}
        self.cat_list = ['prototypes', 'n_build', 'build_times', 'lifetimes']
        for indx, val in enumerate(self.cat_list):
            Label(self.add_inst_window_frame, text=val).grid(row=4, column=indx)
            self.inst_entry_dict[val].append(Entry(self.add_inst_window_frame))
            self.inst_entry_dict[val][-1].grid(row=5, column=indx)
        self.rownum = 6


    def demand_deploy(self):
        if self.inst_name_entry.get() == '':
            messagebox.showerror('Error', 'You must define the institution name before doing this.' )
            return
        guide_text= """Given your current simulation status, this allows you to automatically deploy
        facilities to meet a certain power demand.

        Assumptions:
        Always over-deploy (i.e. Always deploy to have a capacity higher than demand, but just above the demand)
        If demand equation is not defined for a timestep range, the demand is assumed zero, thus nothing happens.
        """
        self.demand_deploy_window = Toplevel(self.master)
        self.demand_deploy_window.title('Demand deployment')
        self.demand_deploy_window.geometry('+100+1000')

        Button(self.demand_deploy_window, text='Done', command=lambda:self.submit_demand()).grid(row=0, column=0)
        Button(self.demand_deploy_window, text='Add row', command=lambda:self.add_demand_row()).grid(row=0, column=1)
        Button(self.demand_deploy_window, text='Visualize', command=lambda:self.visualize_power()).grid(row=0, column=2)

        # Button(self.add_d3ploy_window, text='Done', command=lambda : self.submit_d3ploy(self.d3ploy_entry_dict['institution_name'].get())).grid(row=0, column=0)
        insts_label = Label(self.demand_deploy_window, text='Institutions')
        CreateToolTip(insts_label, text='Institutions to set the demand to.\n`all` takes into account all the institutions.\nThey must be currently existing institutions')
        insts_label.grid(row=1, column=0)
        self.inst_entry = Entry(self.demand_deploy_window)
        self.inst_entry.insert(END, 'all')
        self.inst_entry.grid(row=1, column=1)

        power_cap_varname_label = Label(self.demand_deploy_window, text='Power capacity varnames')
        CreateToolTip(power_cap_varname_label, text='Power capacity variable names.\nIf you are not sure what this is, do not mess with it.')
        power_cap_varname_label.grid(row=2, column=0)
        self.power_cap_varname = Entry(self.demand_deploy_window)
        self.power_cap_varname.insert(END, 'power_cap')
        self.power_cap_varname.grid(row=2, column=1)


        equation_label = Label(self.demand_deploy_window, text='Equation:')
        startime_label = Label(self.demand_deploy_window, text='Start time:')
        endtime_label = Label(self.demand_deploy_window, text='End time:')
        facility_label = Label(self.demand_deploy_window, text='Facility:')
        lifetime_label = Label(self.demand_deploy_window, text='Lifetime')
        ratio_label = Label(self.demand_deploy_window, text='Ratio:')
        CreateToolTip(equation_label, text='Equation for power demand.\nYou can use variables `t` and `e`.\n`t`=absolute timestep\n`e`=2.71828\n(e.g. 100*e**(t/12))')
        CreateToolTip(startime_label, text='Timestep to start applying the demand equation\nStarts from 0.\nTimestep is inclusive.')
        CreateToolTip(endtime_label, text='Timestep to end applying the demand equation.\nTimestep is inclusive.\n(i.e. Your next starttime should be endtime+1)')
        CreateToolTip(facility_label, text='Facility to deploy to meet demand.\nThis can be a space-separated list for multiple facilities\n(e.g. ``reactor1 reactor2``)')
        CreateToolTip(lifetime_label, text='Lifetime of the facilities in timesteps\nThis can also be a space-separated list for multiple facilties\n(e.g. ``960, 360``)')
        CreateToolTip(ratio_label, text='Power ratio of different facilities to deploy to meet demand.\nThis is currently a bit wonky. The demand is simply split into the ratio.\nCurrently looking for better ways to do this.\nThis is ignored if there is only one `facility` parameter.\nThis is also space-separated (e.g. 0.8 0.2)\nIt is automatically normalized.')
        equation_label.grid(row=3, column=0)
        startime_label.grid(row=3, column=1)
        endtime_label.grid(row=3, column=2)
        facility_label.grid(row=3, column=3)
        lifetime_label.grid(row=3, column=4)
        ratio_label.grid(row=3, column=5)
        self.demand_row = 4
        self.demand_cat = ['equation', 'starttime', 'endtime', 'facility', 'lifetime', 'ratio']
        self.demand_entry_dict = {k:[] for k in self.demand_cat}

        self.add_demand_row()


    def add_demand_row(self):
        for indx, val in enumerate(self.demand_cat):
            self.demand_entry_dict[val].append(Entry(self.demand_deploy_window))
            self.demand_entry_dict[val][-1].grid(row=self.demand_row, column=indx)
        self.demand_row += 1


    def parse_entry(self, text):
        text = text.replace(',', ' ')
        w = text.split()
        return w


    def check_deploy_input(self):
        self.insts = self.parse_entry(self.inst_entry.get())
        self.power_varname = self.parse_entry(self.power_cap_varname.get())

        self.demand_dict = {k:[q.get() for q in v] for k, v in self.demand_entry_dict.items()}
        for key in ['facility', 'lifetime', 'ratio']:
            self.demand_dict[key] = [self.parse_entry(q) for q in self.demand_dict[key]]

        e = 2.718
        for i in ['starttime', 'endtime']:
            if not all([self.check_if_int(q) for q in self.demand_dict[i]]):
                messagebox.showerror('Error', 'Your %s definition is not an integer' %i)
                return False
        for i in self.demand_dict['lifetime']:
            for j in i:
                if not self.check_if_int(j):
                    messagebox.showerror('Error', 'Your lifetime definition is not an integer' %i)
                    return False

        # check equation
        if self.duration == 0:
            messagebox.showerror('Error', 'Your must set the simulation parameter, so we know what the duration of the simulation is!')
            return False
        self.demand = np.zeros(self.duration-1)
        for indx, val in enumerate(self.demand_dict['equation']):
            a = int(self.demand_dict['starttime'][indx])
            z = int(self.demand_dict['endtime'][indx])
            if z > self.duration:
                messagebox.showerror('Error', 'Your end time is higher than the duration of:\n %s' %(str(self.duration)))
                return False
            # check if times are sequential
            if val != self.demand_dict['equation'][0]:
                if a <= int(self.demand_dict['starttime'][indx-1]):
                    messagebox.showerror('Error', 'Your start and end times have to be sequential\nYour endtime=%s has to be more than the previous starttime=%s' %(str(self.demand_dict['starttime'][indx-1]), str(a)))
                    return False
            times = list(range(a+1,z+1))
            try:
                print(val)
                print(times)
                print(a,z)
                d = [eval(val) for t in times]
                self.demand[a:z] = d
            except Exception as e:
                print(e)
                messagebox.showerror('Error', 'Demand equation for entry %s:\n%s\n is invalid!' %(str(indx+1), val))
                return False

        # check facility exists?
        for i in self.demand_dict['facility']:
            for j in i:
                if j not in self.proto_dict:
                    messagebox.showerror('Error', 'Facility %s has not been defined.' %i)
                    return False
                if not self.is_any_in_list(self.power_varname, self.proto_dict[j]['config'][self.proto_dict[j]['archetype']]):
                    messagebox.showerror('Error', 'Facility %s does not have any of the power variable name attributes\n%s.' %(j, ' '.join(self.power_varname)))
                    return False

        # check ratio is float
        for indx, val in enumerate(self.demand_dict['ratio']):
            for val2 in val:
                if not self.check_if_float(val2):
                    messagebox.showerror('Error', 'Ratio entry %s:\n%s\nShould be a float' %(str(indx+1), val2))
                    return False

        return True

    def calculate_deploy_data(self):
        # get power capacity values of every facility
        self.power_dict = {}
        if not self.check_deploy_input():
            return False

        for key, val in self.proto_dict.items():
            if self.is_any_in_list(self.power_varname, list(val['config'][self.proto_dict[key]['archetype']].keys())):
                pow_ = 0
                for i in self.power_varname:
                    try:
                        pow_ += float(val['config'][self.proto_dict[key]['archetype']][i])
                    except Exception as e:
                        print(e)
                        print('facility %s does not have parameter %s' %(key, i))
                self.power_dict[key] = pow_
            else:
                continue

        # calculate current supply
        self.current_power = self.get_current_power()
        
        # calculate lack
        # get deployment scheme to make up
        print(self.demand_dict['facility'])
        self.deploy_dict = {k:np.zeros(self.duration-1) for k in list(np.array(self.demand_dict['facility']).flatten())}
        self.deployed_power_dict = {k:np.zeros(self.duration-1) for k in list(np.array(self.demand_dict['facility']).flatten())}
        self.lack = np.array(self.demand) - np.array(self.current_power)
        print('current power ')
        print(self.current_power)
        print(self.lack)
        self.lifetime_dict = {}
        for indx, val in enumerate(list(np.array(self.demand_dict['facility']).flatten())):
            self.lifetime_dict[val] = list(np.array(self.demand_dict['lifetime']).flatten())[indx]
        print(self.lifetime_dict)

        for time in range(len(self.lack)):
            for indx, val in enumerate(self.demand_dict['facility']):
                if int(self.demand_dict['starttime'][indx]) <= time and int(self.demand_dict['endtime'][indx]) >= time:
                    if len(val) == 1:
                        fac = val[0]
                        #while self.lack[time] >= self.power_dict[fac]:
                        while self.lack[time] > 0:
                            self.deploy_dict[fac][time] += 1
                            self.lack[time:time+int(self.lifetime_dict[fac])] -= self.power_dict[fac]
                            self.deployed_power_dict[fac][time:time+int(self.lifetime_dict[fac])] += self.power_dict[fac]
                    else:
                        facs = val
                        # sort fac ascending order by power
                        # facs.sort(key=lambda:i:self.power_dict[i], reverse=True)
                        # there has got to be a better way
                        lack_split = {k:self.lack*v for k,v in zip(facs, [float(q) for q in self.demand_dict['ratio'][indx]])}
                        for indx2, fac in enumerate(facs):
                            # while lack_split[fac][time] >= self.power_dict[fac]:
                            while lack_split[fac][time] > 0:
                                self.deploy_dict[fac][time] += 1
                                self.lack[time:time+int(self.lifetime_dict[fac])] -= self.power_dict[fac]
                                self.deployed_power_dict[fac][time:time+int(self.lifetime_dict[fac])] += self.power_dict[fac]
        return True

    def visualize_power(self):
        if not self.calculate_deploy_data():
            return

        self.plot_window = Toplevel(self.demand_deploy_window)
        self.plot_window.title('Plots')
        self.plot_window.geometry('+100+1000')
        # multiple tabs with multiple plots
        tab_parent = ttk.Notebook(self.plot_window)

        power_tab = Frame(tab_parent)
        tab_parent.add(power_tab, text='Separate Power')
        x = list(range(self.duration-1))
        # stacked bar power plot
        # with demand overlay
        f1 = matplotlib.figure.Figure()
        a1 = f1.add_subplot(111)
        a1.plot(x, self.current_power, label='Current Power')
        for key, val in self.deployed_power_dict.items():
            a1.plot(x, val, label=key+' power')
        if 'all' in self.insts:
            which = 'all institutions'
        else:
            which = 'institutions ' + ' '.join(self.insts)
        a1.set_title('Currently deployed power in %s' %which)
        a1.set_xlabel('Timesteps')
        a1.set_ylabel('Power Capacity')
        a1.grid()
        a1.legend()
        canvas = matplotlib.backends.backend_tkagg.FigureCanvasTkAgg(f1, power_tab)
        canvas.draw()
        canvas.get_tk_widget().pack(side=BOTTOM, fill=BOTH, expand=True)
        
        power_bar = Frame(tab_parent)
        tab_parent.add(power_bar, text='Cumulative Power')
        f2 = matplotlib.figure.Figure()
        a2 = f2.add_subplot(111)
        a2.bar(x, height=self.current_power, width=1, label='current power')
        prev = copy.deepcopy(self.current_power)
        for key, val in self.deployed_power_dict.items():
            a2.bar(x, height=val, width=1, bottom=prev, label=key+' power')
            prev += val
        a2.plot(x, self.demand, label='demand', linestyle='--', color='black')
        a2.set_title('Power capacity')
        a2.set_xlabel('Timesteps')
        a2.set_ylabel('Power Capacity')
        a2.grid()
        a2.legend()
        canvas = matplotlib.backends.backend_tkagg.FigureCanvasTkAgg(f2, power_bar)
        canvas.draw()
        canvas.get_tk_widget().pack(side=BOTTOM, fill=BOTH, expand=True)
        
        dep_plot = Frame(tab_parent)
        tab_parent.add(dep_plot, text='Deployments')
        f3 = matplotlib.figure.Figure()
        a3 = f3.add_subplot(111)
        for key, val in self.deploy_dict.items():
            a3.scatter(x, val, label=key+' deployed', marker='x')
        a3.set_title('Number of facilities deployed')
        a3.set_xlabel('Timesteps')
        a3.set_ylabel('Num. deployed')
        a3.grid()
        a3.legend()
        canvas = matplotlib.backends.backend_tkagg.FigureCanvasTkAgg(f3, dep_plot)
        canvas.draw()
        canvas.get_tk_widget().pack(side=BOTTOM, fill=BOTH, expand=True)
        
        tab_parent.pack(expand=1, fill='both')


    def submit_demand(self):
        if not self.calculate_deploy_data():
            return
        for fac, deploy_timeseries in self.deploy_dict.items():
            for time, n in enumerate(deploy_timeseries):
                if n == 0:
                    continue
                deploy_row = {'build_times': time+1,
                              'prototypes': fac,
                              'lifetimes': self.lifetime_dict[fac],
                              'n_build': int(n)}
                if self.rownum == 6 and self.inst_entry_dict['prototypes'][-1].get() == '':
                    self.rownum += 1
                else:
                    self.add_inst_row()
                for key, val in deploy_row.items():
                    self.inst_entry_dict[key][-1].insert(END, str(val))

        self.demand_deploy_window.destroy()



    def get_current_power(self):

        # now actually do work
        # calculate current capacity
        current_power = np.zeros(self.duration)
        # self.power_dict
        for region in self.region_dict:
            for inst in self.region_dict[region]:
                if inst in self.insts or 'all' in self.insts:
                    for fac in self.region_dict[region][inst]:
                        # [0] prototype name
                        # [1] n_build
                        # [2] entertime
                        # [3] lifetime
                        if fac[0] in self.power_dict:
                            current_power[int(fac[2]): int(fac[2])+int(fac[3])] += self.power_dict[fac[0]] * int(fac[1])
                        else:
                            continue
        return current_power[1:]


    def is_any_in_list(self, list1, list2):
        # checks if at least one element in list1 is in list2
        for i in list1:
            if i in list2:
                return True
        
        return False


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
        print('Done updating the status window')
        self.add_inst_window.destroy()

    def check_if_int(self, string):
        try:
            int(string)
            return True
        except ValueError:
            return False

    def check_if_float(self, string):
        try:
            float(string)
            return True
        except ValueError:
            return False


    def add_inst_row(self):
        for indx, val in enumerate(self.cat_list):
            self.inst_entry_dict[val].append(Entry(self.add_inst_window_frame))
            self.inst_entry_dict[val][-1].grid(row=self.rownum, column=indx)
        self.rownum += 1


    def close_window(self):
        self.master.destroy()

    def guide(self, text=''):
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

        A prototype with a `(undefined)' next to the name ls
        means that the prototype has not
        been defined by the prototype definition section.

        Once done, click Done in the region window.
        """
        if text != '':
            self.guide_window.destroy()
            string = text
        self.guide_window = Toplevel(self.master)
        self.guide_window.title('Region guide')
        self.guide_window.geometry('+0+400')
        Label(self.guide_window, text=string).pack(padx=30, pady=30)

