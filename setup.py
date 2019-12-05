from setuptools import setup, find_packages

setup(name='cyclus_gui',
      version='0.1',
      description='Graphical User Interface for Cyclus',
      url='code.ornl.gov/4ib/cyclus_gui',
      packages=find_packages(),
      package_data={'': ['*.csv', '*.json', '*.sh', '*.xml']},
      include_package_data=True      
      )