import numpy as np
import unittest
#import cyclus_gui.gui.gui
from cyclus_gui.gui.sim_window import SimulationWindow
from cyclus_gui.gui.arche_window import ArchetypeWindow
from cyclus_gui.gui.proto_window import PrototypeWindow
from cyclus_gui.gui.region_window import RegionWindow
from cyclus_gui.gui.recipe_window import RecipeWindow
from cyclus_gui.gui.backend_window import BackendWindow
import os
import shutil
from tkinter import *
import xmltodict

## go from start to finish
here = os.path.dirname(os.path.abspath(__file__))

uniq_id = 'test'
root = Tk()
output_path = os.path.join(here, 'output_test')
if os.path.isdir(output_path):
    shutil.rmtree(output_path)
os.mkdir(output_path)

def test_simulation(root, output_path):
    #simulation 
    #obj.open_window('simulation', output_path)
    # simulation window object
    obj = SimulationWindow(root, output_path)
    obj.entry_dict['duration'].insert(END, 320)
    obj.entry_dict['startmonth'].insert(END, 1)
    obj.done()

    # check output
    xml_dict = xmltodict.parse(open(os.path.join(output_path, 'control.xml')).read())['control']
    answer_dict = {'duration': 320,
                   'startmonth': 1,
                   'startyear': 2019,
                   'decay': 'lazy'}
    for k, v in answer_dict.items():
        if xml_dict[k] != str(v):
            print('Input %s Should be %s, it is written as %s' %(k, v, xml_dict[k]))
            return False
    return True



