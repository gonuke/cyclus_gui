# Cyclus - Workbench Integration

You can download workbench from [the ORNL gitlab](https://code.ornl.gov/neams-workbench/downloads/-/tree/master).

## Known bugs

1. If you run on python3, and errors when you run `generate_cyclus_sch.py` on `xml2obj`, try with python 2.

## Steps

1. Go into `generate_cyclus_sch.py` and go to the very bottom, modify `path` to your workbench rte path.
2. Run `python generate_cyclus_sch.py`. This script will:
    - Try to get the metadata from your Cyclus installation (Running `cyclus -m`)
        - If this fails, it will just use the pre-shipped file (`m.json`)
        - If you have it set up differently, change the `cyclus_cmd` variable.
    - It will generate the following files into your respective workbench directories:
        - Grammar file (`cyclus.wbg`)
            - This file tells Workbench what files are needed
            - and what syntax the input helper would use
        - Schema file (`cyclus.sch`)
            - schema file has all the rules for syntax validation
            - and template pointers
        - Template file
            - Every archetype gets a template, so it's easier for users to know what attributes each has.
            - It also comes with the docstring
        - Highlight file
            - This file defines different coloring (e.g. for comments, brackets etc.)
        - Cyclus runner (`cyclus.py`)
            - The runner is the part that `talks` to Workbench
            - The runner has modules for taking in executables,
            - running cyclus remotely / locally
            - Converting files from SON to JSON
        - Cyclus processor (`cyclus_processor.py`, `cyclus.wbp`)
            - This is not used, due to some bugs.
3. Open Workbench, click on `file -> configurations`.
4. On the very top row, click `Add..` to add Cyclus
5. Configure your executable path, and if you're using a remote server to run your jobs, fill out the remote server address, username, and password
6. Create a new file, with extension `.cyclus`
7. Note that the text format will not be acceptable by Cyclus. `cyclus.py` will convert the SON file format to JSON readable for Cyclus.
8. If not already, click the dropdown next to `Processors` and choose Cyclus.
9. On the text editor, press `control + space` (for mac, other OSs look at `Edit -> Autocomplete` for shortcut)
10. click `simulation`, and the initial template will (hopefully) take it from there.
11. Notice the `validation` tab on the bottom, it will tell you if there's something wrong.
12. Note that if you have validation errors in the block you've been working on, Autocomplete won't work elsewhere.
13. Once finished, click `Run`. That will do:
    - convert the current SON file you have to a JSON, and clean it up (outputs as `[your_filename].json`)
    - if you defined a remote address:
        - uploads the .json file into `/home/[username]/[some_hash]/input.json`
        - runs cyclus
        - downloads the output to `[your_filename].sqlite`
    - if you didn't:
        - runs cyclus by `[your_executable_command] [your_filename].json -o [your_filename].sqlite`

## PS

The postprocessor was written, and it does:
- Reads the .sqlite file and generates a long .csv file with 'important metrics' such as material flow
- Workbench can read those .csv files (but not .sqlite files, thus the conversion) and display them as plots and tables.

It is currently commented out in `cyclus.py` (in function `postrun`), but feel free to play with it and see if it's worth it. I'd encourage eventual integration of Cymetric, obviously.