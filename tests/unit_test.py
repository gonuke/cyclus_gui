import numpy as np
import unittest
from cyclus_gui.gui.sim_window import SimulationWindow
from cyclus_gui.gui.arche_window import ArchetypeWindow
from cyclus_gui.gui.proto_window import PrototypeWindow
from cyclus_gui.gui.region_window import RegionWindow
from cyclus_gui.gui.recipe_window import RecipeWindow
from cyclus_gui.gui.backend_window import BackendWindow



def skip_init(cls):
    actual_init = cls.__init__
    cls.__init__ = lambda *args, **kwargs: None
    instance = cls()
    cls.__init__ = actual_init
    return instance

class sim_unit_test(unittest.TestCase):
   
    def test_is_it_pos_integer(self):
        obj = skip_init(SimulationWindow)
        q_a_dict = {1:True,
                    2.1:False,
                    -1:False,
                    4:True}
        for key, val in q_a_dict.items():
            self.assertEqual(obj.is_it_pos_integer(key), val)




if __name__ == '__main__':
    unittest.main()