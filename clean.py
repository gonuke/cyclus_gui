import shutil
import os
here = os.path.dirname(os.path.abspath(__file__))
files = os.listdir(here)
for i in files:
    if 'output_' in i:
        if '53d' not in i and '41c' not in i:
            shutil.rmtree(i)
    if '__py' in i:
        shutil.rmtree(i)