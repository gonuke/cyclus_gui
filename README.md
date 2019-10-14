# Cyclus Graphical User Interface

This module is a Graphical User Interface (GUI) for Cyclus input generation
and output visualization. Users can generate a Cyclus input file with
dropdown menus and filling in blanks for user parameters.

# How it runs Cyclus without Cyclus

We created a MS Azure VM that has Cyclus (and others like Cycamore, etc)
pre-built. The GUI accesses that VM, runs the generated input, and retrieves
the output.

## Dependencies
Cyclus
Cycamore
tkinter



## Reported Bug with OSX Mojave (10.14.6)
If running `python gui.py` crashes and logs you off, try downgrading your python to 3.70. I did it using a conda environment.