#!/usr/bin/python
"""WorkbenchRuntimeEnrivonment"""
import argparse
import time
import getpass
import json
import os
import platform
import shutil
import stat
import paramiko
import http.client
import subprocess
import uuid
import sys
import tempfile
import threading
        
def unpack_stringlist(stringlist):
    """parses stringlist that was formatted to pass on command-line into original array of strings"""
    if stringlist is None or stringlist == '':
        return None
    # if isinstance(stringlist,basestring):
    #     no change
    if not isinstance(stringlist,str) and not isinstance(stringlist,basestring):
        raise ValueError("Method unpack_stringlist requires a string.  Found a " + str(type(stringlist)))
    stringlist = stringlist.lstrip("'").rstrip("'")
    stringlist = stringlist.replace("__squote__","'")
    return stringlist.split("__delim__")


def pack_stringlist(stringlist):
    """formats a stringlist to pass on command-line"""
    if stringlist is None or stringlist == '':
        return None
    if isinstance(stringlist,list):
        stringlist = '__delim__'.join(stringlist)
    return "'" + stringlist.replace("'","__squote__") + "'"

def create_directory(directory):
    """creates the requested directory path"""
    # path is not an existing directory
    if not os.path.isdir(directory):
        # path exists, this is an error
        if os.path.exists(directory):
            # print error message and quit...
            print ("Error: specified directory path ({0}) exists but is not a " \
                  "directory".format(directory))
            sys.exit(1)
        # path doesn't exist, try to create it
        else:
            # catch errors...
            os.makedirs(directory)

def expand(expanding, variables):
    """expand the given string using the given variables"""
    # find right-most start of variable pattern
    start = expanding.rfind("${")

    # keep searching while we find variable patterns
    while start >= 0:
        # find left-most end of variable pattern (starting at current position)
        end = expanding.find("}", start + 1)

        # stop if no end was found
        if end < 0:
            break

        # variable name
        variable = expanding[start+2:end]

        # variable value
        if variable in variables:
            value = variables[variable]
        else:
            value = ""

        # replace the variable with its value and continue searching
        expanding = expanding[:start] + value + expanding[end+1:]
        start = expanding.rfind("${")
    return expanding

def reader(sin, lines):
    """read each line from sin and add to lines"""
    # read the first line
    line = sin.readline()

    # read/write lines until no more can be read
    while line:
        # store last line, read next line
        lines.append(line)
        line = sin.readline()

    # close input if not closed
    if not sin.closed:
        sin.close()

def streamer(sin, sout, tout=None):
    """forward input stream to output stream (and optional 'tee-out')"""
    # read the first line
    line = sin.readline()

    # read/write lines until no more can be read
    while line:
        # write the last line read, flush to ensure it's written
        sout.write(line)
        sout.flush()

        # tout (tee-out) is valid, write to it
        if tout:
            tout.write(line)
            tout.flush()

        # read next line
        line = sin.readline()

    # close input if not closed
    if not sin.closed:
        sin.close()

def which(exe):
    """locate the given executable via the environment, if necessary"""
    # platform-specific executable checks
    is_windows = platform.system() == "Windows"
    if is_windows:
        exe_check = lambda p: (os.stat(p)[0] & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)) != 0
    else:
        exe_check = lambda p: os.access(p, os.X_OK)

    # determine whether the given path is an executable file
    is_exe = lambda p: os.path.isfile(p) and exe_check(p)

    # treat the given executable as a path
    path = os.path.realpath(exe)

    # this is an executable, early exit
    if is_exe(path):
        return path

    # not an executable, search environment via PATH
    for node in os.getenv("PATH", "").split(os.pathsep):
        # test executable path
        path = os.path.realpath(os.path.join(node, exe))

        # path is an executable, return it
        if is_exe(path):
            return path
        if is_windows and is_exe(path+".exe"):
            return path+".exe"

    # no suitable executable found
    return None

class RunOptions(object):
    """stores per-input run options"""
    def __init__(self):
        self.input = None
        self.input_directory = None
        self.output_basename = None
        self.output_directory = None
        self.working_directory = None

class WorkbenchRuntimeEnvironment(object):
    """base runtime environment class"""
    def __init__(self):
        # Capture RTE directory
        __file__ = '/Users/4ib/Desktop/git/cyclus_gui/neams'
        self.rte_dir = os.path.dirname(os.path.abspath(__file__))
        # initialize attributes
        self.additional = None
        self.cleanup = True
        self.executable = None
        self.inputs = []
        self.json = False
        self.grammar_path = "None"
        self.options = {"shared": [], "unique": []}
        self.output_basename = None
        self.output_directory = None
        self.tee = False
        self.timestamp = False
        self.verbosity = 0
        self.working_directory = None

    def set_executable(self, executable):
        self.executable = executable
    def add_arguments(self, parser):
        """adds default (known) arguments"""
        for option_type in self.options:
            for option in self.options[option_type]:
                # skip empty options
                if not bool(option):
                    continue

                # clone current option for modification
                clone = dict(option)

                # capture flag, if specified
                if "flag" in clone:
                    flag = clone["flag"]

                # remove all fields
                for key in ["deprecated", "flag", "name"]:
                    if key in clone:
                        del clone[key]

                # modify 'type' field to be a callable
                if "type" in clone:
                    # cached 'type' field
                    cached = clone["type"]

                    # modify 'type' field for the arg parser
                    if cached == "bool":
                        del clone["type"]
                    elif cached == "float":
                        clone["type"] = float
                    elif cached == "int":
                        clone["type"] = int
                    elif cached == "string" or cached == "stringlist":
                        clone["type"] = str

                # parse args
                parser.add_argument(flag, **clone)

    def __add_options(self):
        """private method to add 'shared' options"""
        shared = self.options["shared"]

        shared.append({
            "default": self.additional,
            "flag": "additional",
            "help": "Additional arguments to pass to the executable",
            "metavar": "arg",
            "name": "Additional Arguments",
            "nargs": "*",
            "type": "stringlist"
        })
        shared.append({
            "default": self.executable,
            "dest": "executable",
            "flag": "-e",
            "help": "Path to the executable to run",
            "metavar": "executable",
            "name": "Executable",
            "required": True,
            "type": "string"
        })
        shared.append({
            "default": None,
            "dest": "inputs",
            "flag": "-i",
            "help": "Path(s) to input file(s)",
            "metavar": "input_file",
            "name": "Input(s)",
            "nargs": "+",
            "required": True,
            "type": "string"
        })
        shared.append({
            "action": self.print_options(),
            "default": self.json,
            "dest": "json",
            "flag": "-json",
            "help": "Print available options in JSON format and quit",
            "nargs": 0,
            "type": "bool"
        })
        shared.append({       
            "action": self.__grammar(),     
            "default": self.grammar_path,
            "dest": "grammar_path",
            "flag": "-grammar",
            "help": "Print the path the application's input grammar file path, \
                     only if the given file is older than the input grammar",
            "type": "string"
        })
        shared.append({
            "action": "store_true",
            "default": not self.cleanup,
            "dest": "cleanup",
            "flag": "-k",
            "help": "Keep the working directory after execution finishes",
            "name": "Save Working Directory",
            "type": "bool"
        })
        shared.append({
            "default": self.output_basename,
            "dest": "output_basename",
            "flag": "-o",
            "help": "Name of the generated output file. "
                    "If it is an absolute or relative path, it overrides output_directory.",
            "metavar": "output_basename",
            "name": "Output Basename",
            "type": "string"
        })
        shared.append({
            "default": self.output_directory,
            "dest": "output_directory",
            "flag": "-O",
            "help": "Directory in which to store the output",
            "metavar": "output_directory",
            "name": "Output Directory",
            "type": "string"
        })
        shared.append({
            "action": "store_true",
            "default": self.timestamp,
            "dest": "timestamp",
            "flag": "-t",
            "help": "Whether to timestamp the working directory, output files, etc.",
            "name": "Timestamp",
            "type": "bool"
        })
        shared.append({
            "default": self.verbosity,
            "dest": "verbosity",
            "flag": "-v",
            "help": "Level of verbosity when logging information (higher values = more messages)",
            "metavar": "verbosity_level",
            "name": "Verbose Level",
            "type": "int"
        })
        shared.append({
            "default": self.working_directory,
            "dest": "working_directory",
            "flag": "-w",
            "help": "Directory in which to run the executable (implies -k)",
            "metavar": "working_directory",
            "name": "Working Directory",
            "type": "string"
        })

        # app-specific options
        self.options["unique"] = self.app_options()

    def print_options(self):
        """dump a JSON packet of supported options"""
        # reference to self.options
        opts = self.options
        env = self.environment()

        class OptionsAction(argparse.Action):
            """action class to dump supported options in a proper format"""
            def __call__(self, parser, namespace, values, option_string=None):
                # dicts containing supported options
                options = {}

                # populate based on member's keys
                for key in opts.keys():
                    options[key] = []

                # supported keys
                supported = ["default", "flag", "help", "name", "type"]

                # loop over given options to determine which are supported for output
                for group in opts.keys():
                    # loop over each option in this group
                    for option in opts[group]:
                        # only add option if it has a 'name' entry
                        if "name" in option:
                            # option dict to retain
                            custom = {}

                            # only include supported keys
                            for key in supported:
                                # store known keys
                                if key in option:
                                    # store key/value
                                    custom[key] = option[key]

                            # add to options
                            options[group].append(custom)

                print (json.JSONEncoder().encode({
                    "options": options,
                    "environment": env
                }))
                sys.exit(0)

        return OptionsAction

    def __grammar(self):
        """dump a SON-formatted input grammar to the provided file"""        
        class OptionsAction(argparse.Action):
            """action class to dump grammar to provide file"""
            def __call__(self, parser, namespace, values, option_string=None):
                grammar_path = values
                namespace.update_and_print_grammar(grammar_path)                
                sys.exit(0)

        return OptionsAction
    
    def update_and_print_grammar(self, grammar_path):
        """Checks the provided grammar file and determines if it is out of date
        and if so, updates it accordingly"""
        print (grammar_path)
        return

    def get_grammar_additional_resources(self, grammar_file_path):
        """Returns a list of filepaths that need included which are not normally
         included"""
        return None

    def app_name(self):
        """returns the app's self-designated name"""
        return "cyclus"

    def app_options(self):
        """list of app-specific options"""
        unique = []
        unique.append({
            "default": '',
            "dest": "remote_server_address",
            "flag": "-r",
            "help": "Remote server address",
            "metavar": "remote_server_address",
            "name": "Remote Server Address",
            "type": "string"
        })
        unique.append({
            "default": '',
            "dest": "remote_server_username",
            "flag": "-u",
            "help": "Remote server username",
            "metavar": "remote_server_username",
            "name": "Remote Username",
            "type": "string"
        })
        unique.append({
            "default": '',
            "dest": "remote_server_password",
            "flag": "-p",
            "help": "Remote server password",
            "metavar": "remote_server_password",
            "name": "Remote Password",
            "type": "string"
        })
        # this is for proxy and other techniques
        unique.append({
            "default": '',
            "dest": "proxy_hostname",
            "flag": "-ph",
            "help": "SSH proxy hostname",
            "metavar": "proxy_hostname",
            "name": "SSH Proxy Hostname",
            "type": "string"
        })
        unique.append({
            "default": '',
            "dest": "proxy_port",
            "flag": "-pp",
            "help": "SSH proxy port",
            "metavar": "proxy_port",
            "name": "SSH Proxy Port",
            "type": "string"
        })
        
        return unique

    def echo(self, level, *args):
        """print messages to the console (based on verbosity)"""
        if self.verbosity >= level:
            print ("".join(args))

    def environ(self, _input):
        """generate a subprocess' environment"""
        env = os.environ

        # init known variables
        env["APP_NAME"] = self.app_name()
        env["INPUT_BASENAME"] = os.path.splitext(os.path.basename(_input))[0]
        env["PID"] = str(os.getpid())
        env["UID"] = getpass.getuser()

        return env

    def environment(self):
        """generate a dict of supported environment variables"""
        return {}

    def execute(self, args):
        """execute the runtime per given input"""
        # parse/process arguments
        parser = argparse.ArgumentParser(description="Runtime Environment")

        self.__add_options()
        self.add_arguments(parser)
        self.process_args(parser, args)

        
        # execute each input
        for _input in self.inputs:
            # input-specific excution environment
            env = self.environ(_input)

            # current input's options
            options = RunOptions()

            options.input = os.path.abspath(expand(_input, env))
            options.input_directory = os.path.abspath(os.path.dirname(options.input))
            options.output_basename = expand(self.output_basename
                                             if self.output_basename
                                             else "${INPUT_BASENAME}", env)
            options.output_directory = expand(self.output_directory
                                              if self.output_directory
                                              else options.input_directory, env)
            options.working_directory = expand(os.path.join(self.working_directory,
                                                            "${APP_NAME}.${UID}.${PID}"), env)

            # cache current working directory
            cwd = os.getcwd()

            # exeute input
            self.prerun(options)
            self.run(options)
            self.postrun(options)

            # change to cached working directory so cleanup can happen
            os.chdir(cwd)

            # perform cleanup?
            if self.cleanup and os.path.exists(options.working_directory):
                shutil.rmtree(options.working_directory)

    def output_basename_overridden(self):
        """determines whether the output_basename field was overridden"""
        return self.output_basename != None

    def output_directory_overridden(self):
        """determines whether the output_directory field was overridden"""
        return self.output_directory != None

    def postrun(self, options):
        """actions to perform after the run finishes"""

    def prerun(self, options):
        """actions to perform before the run starts"""
        self.echo(1, "#### Pre-run ####")

        # ensure output directory exists
        self.echo(1, "# Ensuring output directory exists...")
        create_directory(options.output_directory)
        self.echo(2, "#   ", options.output_directory)

        # ensure working directory exists, navigate to it
        self.echo(1, "# Ensuring current working directory exists...")
        create_directory(options.working_directory)
        self.echo(2, "#   ", options.working_directory)
        os.chdir(options.working_directory)

        self.echo(1, "#### Pre-run ####")
        self.echo(1)

    def process_args(self, parser, args):
        """parse/process the arguments"""
        self.echo(1, "#### Processing arguments ####")

        # parse args
        parser.parse_args(args=args, namespace=self)
        
        # check if it is remote run or local run
        if self.remote_server_address:
            self.is_remote = True
            self.echo(1, '# Remote Execution Enabled.')


        if self.is_remote:
            # this remote execution assumes that the remote server is a UNIX environment,
            # only tested on Ubuntu.
            try:
                # check if the executable exists:
                self.ssh = paramiko.SSHClient()
                self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                self.echo(1, '# Attempting to connect to %s' %self.remote_server_address)
                self.echo(1, '# As user "%s"' %self.remote_server_username)
                self.echo(1, '# With password "%s"' %self.remote_server_password)
                if self.proxy_hostname:
                    self.echo(1, '# With proxy hostname "%s"' %self.proxy_hostname)
                    self.echo(1, '# With proxy port "%s"' %self.proxy_port)
                    http_con = http.client.HTTPConnection(self.proxy_hostname, self.proxy_port)
                    http_con.set_tunnel(self.remote_server_address, 22, {})
                    http_con.connect()
                    sock = http_con.sock
                    self.ssh.connect(self.remote_server_address, username=self.remote_server_username,
                                     password=self.remote_server_password, sock=sock,
                                     allow_agent=False, look_for_keys=False)
                else:
                    self.ssh.connect(self.remote_server_address, username=self.remote_server_username,
                                     password=self.remote_server_password,
                                     allow_agent=False, look_for_keys=False)

                self.echo(1, '# Connected.')
                self.echo(1, '# Testing if the executable exists...')
                # check if file is executable
                output = self.remote_execute('test -x %s && echo "yayyy"' %self.executable)
                if 'yay' in output:
                    self.echo(1, '# The file in the defined path is executable.')
                else:
                    self.echo(0, 'The file is not Executable')
                    sys.exit(1)
            except Exception as e:
                self.echo(0, 'Could not connect. Check arguments.')
                self.echo(0, 'See Error below:')
                self.echo(0, e)
                sys.exit(1)

        else:
            self.echo(1, "# Expanding executable path using environment variables")
            self.executable = expand(os.path.expanduser(self.executable), os.environ)
            self.echo(2, "#   Executable: ", self.executable)
            # look for valid executable
            self.echo(1, "# Checking whether ", self.executable, " is executable")
            exe = which(self.executable)
            self.echo(2, "#   Executable: ", exe)
            
            # verify executable can be executed
            if not exe:
                print ("Error: specified executable ({0}) is not a valid, executable " \
                      "file".format(self.executable))
                sys.exit(1)
            # update with full path to executable
            self.executable = exe

        # output directory specified
        if self.output_directory:
            self.echo(1, "# Fixing up output_directory...")
            # expand env vars/user-area prefix(es), convert to absolute path
            self.output_directory = expand(self.output_directory, os.environ)
            self.output_directory = os.path.expanduser(self.output_directory)
            self.output_directory = os.path.abspath(self.output_directory)
            self.echo(2, "#   ", self.output_directory)

        # a relative or absolute path in output_basename overrides the output_directory
        if self.output_basename:
            self.echo(1, "# Fixing up output_basename...")
            # expand env vars/user-area prefix(es), normalize path
            self.output_basename = expand(self.output_basename, os.environ)
            self.output_basename = os.path.expanduser(self.output_basename)
            self.output_basename = os.path.normpath(self.output_basename)
            self.echo(2, "#   ", self.output_basename)

            # split into parent/child paths
            (parent, child) = os.path.split(self.output_basename)

            # there was a parent directory, override output_directory
            if parent:
                self.echo(1, "# output_basename overriding output_directory...")
                self.output_directory = os.path.abspath(parent)
                self.output_basename = child
                self.echo(2, "#   ", self.output_directory, " ... ", self.output_basename)

        self.echo(1, "# Ensuring root working directory exists...")

        # working directory specified, ensure it exists
        if self.working_directory:
            # expand env vars/user-area prefix(es), convert to absolute path
            self.working_directory = expand(self.working_directory, os.environ)
            self.working_directory = os.path.expanduser(self.working_directory)
            self.working_directory = os.path.abspath(self.working_directory)

            # create working directory, override cleanup flag
            create_directory(expand(self.working_directory, os.environ))
            self.cleanup = False
        # working directory not specified, default to a temp directory
        else:
            self.working_directory = tempfile.gettempdir()

        self.echo(2, "#   ", self.working_directory)
        self.echo(1, "#### Processing arguments ####")
        self.echo(1)

    def remote_execute(self, cmd):
        i, o, e = self.ssh.exec_command(cmd)
        output = '\n'.join(o.readlines())
        error = '\n'.join(e.readlines())
        if len(error) != 0:
            return error
        return output


    def run(self, options):
        """run the given executable"""
        self.echo(1, "#### Run ", self.app_name(), " ####")

        # list of arguments to pass when launching the executable
        # If the executable is a python script, make sure to use
        # Workbench's python environment as this is likely more
        # recent and contains packages that are not available
        # with default Python installations
        print(self.executable)
        if self.executable.endswith(".py"):
            args = [sys.executable, self.executable]
        else:
            args = [self.executable]

        # pass 'additional' to the executable if given
        if self.additional:
            args.extend(self.additional)
        # request list of supported arguments to pass to the executable
        args.extend(self.run_args(options))
        print('args')
        print(args)
        if self.is_remote:
            self.echo(1, "#### Executing '", " ".join(args), "' on remote server %s " %self.remote_server_address)
            rtncode = 0
            try:
                # since we checked the connection from the checking executable part,
                # that part can be skipped
                # upload file
                duplicate_hash = True
                # just in case the hash exists
                n =0 
                import os
                while duplicate_hash and n < 3:
                    rnd_dir = os.path.join('/home/', self.remote_server_username, str(uuid.uuid4()))
                    remote_input_path = os.path.join(rnd_dir, 'input.xml')
                    remote_output_path = remote_input_path.replace('.xml', '.sqlite')
                    output = self.remote_execute('mkdir %s' %rnd_dir)
                    print('error', output)
                    n+=1
                    if not output:
                        # empty output means nothing went wrong,  
                        duplicate_hash = False
                self.echo(1, '# Uploading input file to %s' %self.remote_server_address)
                self.echo(1, '# To path "%s"' %remote_input_path)
                ftp = self.ssh.open_sftp()
                ftp.put(options.input ,remote_input_path)

                self.echo(1, '# Now running %s...' %self.app_name())
                output = self.remote_execute('%s %s -o %s --warn-limit 0' %(self.executable, remote_input_path, remote_output_path))
                # this is super wonky, consider changing
                if output == 0 or ('Error' not in output and 'error' not in output and 'Abort' not in output and 'fatal' not in output and 'Invalid' not in output):
                    
                    self.echo(1, '############################' )
                    self.echo(1, '# %s ran successfully!' %self.app_name())
                    self.echo(1, '############################' )
                    
                    self.echo(1, '# Now downloading output file')
                    pre, ext = os.path.splitext(options.input)
                    ftp.get(remote_output_path, os.path.join(self.working_directory, pre + '.out'))
                    # this is super wonky, consider changing
                    time.sleep(5)
                    self.echo(1, '# Download complete (%s)' %os.path.join(self.working_directory, pre + '.out'))

                else:
                    self.echo(1, '# Run Failed! See the following output')
                    self.echo(1, output)

            except Exception as e:
                self.echo(0, 'Something Went Wrong')
                self.echo(0, 'See Error below:')
                print(e)
                self.echo(0, e)
                sys.exit(1)

        else:
            # local run
            self.echo(1, "#### Executing '"," ".join(args),"'")
            # execute
            rtncode = 0
            try:
                proc = subprocess.Popen(args, bufsize=0, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

                # tee-output objects
                teeout = None
                teeerr = None

                # tee requested
                if self.tee:
                    teeout = open(options.output_basename + ".out", "w")
                    teeerr = open(options.output_basename + ".err", "w")

                # start background readers
                out = threading.Thread(target=streamer, name="out_reader",
                                   args=(proc.stdout, sys.stdout, teeout))
                err = threading.Thread(target=streamer, name="err_reader",
                                   args=(proc.stderr, sys.stderr, teeerr))
                out.start()
                err.start()

                # wait for process to finish
                proc.wait()
                out.join()
                err.join()
                rtncode = proc.returncode
            except:
                # On some systems with limited or no network access the subprocess module
                # may have failed to install properly. This is a fall back strategy 
                import os
                rtncode = os.system(" ".join(args))

                self.echo(1, "# Finished running ", self.app_name(), " with exit code ",
                          str(proc.returncode))
                self.echo(1)

    def run_args(self, options):
        """returns a list of arguments to pass to the given executable"""
        return [options.input]

    def strip_unit_of_execution(self, filename, unit_name, strip_son=False):
        """Removes the unit of execution delimiters.
        =unit_name
        ...
        end
        These two lines will be replaced with empty lines.
        If these exist, this function returns a new filename
        to a 'clean' file.
        If no delimiters were encountered, None is returned
        """
        # must determine if this has runtime constructs '^=unit_name'
        # terminated by '^end'. This is not native
        # and must be removed
        has_rt_delimiters = False # assume no '=unit_name...end' exists

        if strip_son:
            self.echo(1, "Removing Standard Object Delimiters...")

        with open(filename, 'r') as input_file:
            # consume the entire file
            input_file_lines = input_file.readlines()
            index = 0

            for line in input_file_lines:
                stripped_line = line.strip().lower()

                if strip_son:
                    input_file_lines[index] = input_file_lines[index].replace("{", " ")
                    input_file_lines[index] = input_file_lines[index].replace("}", " ")
                    input_file_lines[index] = input_file_lines[index].replace("]", " ")
                    input_file_lines[index] = input_file_lines[index].replace("[", " ")
                    input_file_lines[index] = input_file_lines[index].replace("= YES", "    ")
                    has_rt_delimiters = True

                if stripped_line == "=" + unit_name:
                    has_rt_delimiters = True
                    # Replace runtime delimiter with empty space
                    input_file_lines.pop(index)
                    input_file_lines.insert(index, "")
                elif stripped_line == "end":
                    has_rt_delimiters = True
                    # Replace runtime delimiter with empty space
                    input_file_lines.pop(index)
                    input_file_lines.insert(index, "")

                index += 1

        # if the delimiters are present write the clean file
        if has_rt_delimiters:
            clean_input_file_name = filename + ".cleaned"
            self.echo(1, " -- Runtime construct discovered, producing ", clean_input_file_name)

            with open(clean_input_file_name, 'w') as cleaned_input_file:
                for line in input_file_lines:
                    cleaned_input_file.write(line)

            # update the input file to be the cleaned version
            return clean_input_file_name

        # if no stripping occurred, None is the response
        return None

    def working_directory_overridden(self):
        """determines whether the working_directory field was overridden"""
        return self.working_directory != tempfile.gettempdir()

    def exit_gracefully(self, signum, frame):
        """Cleanup steps to perform after receiving the SIGTERM signal"""
        return

if __name__ == "__main__":
    # from util.check_version import CheckVersion
    # CheckVersion.check()
    import signal
    rte = WorkbenchRuntimeEnvironment()
    signal.signal(signal.SIGTERM, rte.exit_gracefully)
    signal.signal(signal.SIGINT, rte.exit_gracefully)
    # execute runtime, ignoring first argument (the python script itself)
    rte.execute(sys.argv[1:])
