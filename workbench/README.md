# Cyclus - Workbench Integration

You can download workbench from [the ORNL gitlab](https://code.ornl.gov/neams-workbench/downloads/-/tree/master).

Once you download it, locate where the `rte` folder. You are going to add the contents of this repo to this directory. 

## cyclus_simple.py
Runtime file. Move this to your rte directory in workbench, and set the paths in the file so that it will find the other file-generating scripts in `.../cyclus_gui/workbench/cyclus`

Clikcing on `update and print grammar` on workbench will populate the files need for the template, autofill, and so on.
