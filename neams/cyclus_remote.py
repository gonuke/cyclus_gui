#!/usr/bin/python
"""SetupRemoteRuntimeEnvironment"""

# standard imports
import os
import sys
from util.abstract_remote import AbstractRemoteRuntimeEnvironment, Const, RemoteConstants, get_rte_remote_resource_dir
from util.util import Utilities
from hello_world import TeeStdout

# super import
from workbench import pack_stringlist, which
from workbench import *

class SetupRemoteRuntimeEnvironment(WorkbenchRuntimeEnvironment):
    """runtime environment for configuring other runtimes for remote execution"""

    _cfg_packet_filepath = None
    _server_execution_dir = None
    _application_name = None
    _remote_application_name = None
    _application_path = None
    _deploy_to_server = False
    _override_existing_deployments = False
    _verify_connection = True
    _runtime_command = None
    _upload_patterns = None
    _download_patterns = None
    _tail_file = None
    _header_lines = None
    _scheduler_type = None
    __input_dict = None
    __input_filepath = None
    _tee_out = None

    def __init__(self):
        # call super class constructor
        super(SetupRemoteRuntimeEnvironment, self).__init__()
        self.cleanup = False

    # def __add_options(self):
    #     """overriding private method from WorkbenchRuntimeEnvironment"""
    #     super(SetupRemoteRuntimeEnvironment, self).__add_options()
    #     shared = self.options["shared"]
    #     self.echo(0,str(shared))
    #     for opt in shared:
    #         self.echo(0,"hw try")
    #         if isinstance(opt, dict) and "metavar" in opt and opt["metavar"] == "executable":
    #             self.echo(0,"removing " + str(opt))
    #             shared.remove(opt)
    #             break
    """!
    def update_and_print_grammar(self, grammar_path):
        this_grammar_path = os.path.join(self.rte_dir,"setup_remote","grammars","setup_remote.wbg")
        this_schema_path = os.path.join(self.rte_dir,"setup_remote","schema","setup_remote.sch")
        this_grammar_mtime = os.path.getmtime(this_grammar_path)
        this_schema_mtime = os.path.getmtime(this_schema_path)
        try:
            workbench_grammar_mtime = os.path.getmtime(grammar_path)
        except OSError:
            # indicate grammar file is 'way old' 
            # which will indicate it needs to be updated
            workbench_grammar_mtime = 0

        # Update Workbench's grammar status file        
        if this_grammar_mtime > workbench_grammar_mtime or this_schema_mtime > workbench_grammar_mtime:
            this_grammar_name = os.path.basename(grammar_path).replace(".wbg","")
            with open(grammar_path,"w") as workbench_grammar_file:
                workbench_grammar_file.write("name='{}' redirect='{}'".format(this_grammar_name, this_grammar_path))
            print (grammar_path)   
    """!
    def app_name(self):
        """returns the app's self-designated name"""
        return "cyclus"

    def app_options(self):
        """list of app-specific options"""
        opts = []

        # opts.append({
        #     "default": self.alias,
        #     "dest": "alias",
        #     "flag": "-a",
        #     "help": "Specify path to alias file",
        #     "metavar": "alias_file",
        #     "name": "Alias File Path",
        #     "type": "string"
        # })

        return opts

    def environment(self):
        """generate a dict of the supported environment variables"""
        return {}

    def prerun(self, options):
        """actions to perform before the run starts"""
        # we are really only using one input file
        _input = self.inputs[0]
        # copy the input to the output
        output_filepath = _input + ".out"
        from shutil import copy
        copy(_input, output_filepath)

        # redirect stderr to stdout
        sys.stderr = sys.stdout
        # tee stdout
        self._tee_out=TeeStdout(output_filepath, 'a')
        self.echo(0,"\n\nSaving output to "+output_filepath+"\n\n")
        import platform
        self.echo(0, "Python version: " + str(platform.python_version()) + "\nPython executable: " + str(sys.executable) + "\nPlatform name: " + str(sys.platform) + "\n")

    def get_version(self,input_filepath):
        return self.get_dict_from_input_path(input_filepath)["setup_properties"]['version_number']['value']

    def get_dict_from_input_path(self,input_filepath):
        if self.__input_dict is None:
            #! change shcema filepath
            pdir = os.path.join(os.path.dirname(os.path.abspath(__file__)))
            schema_filepath = os.path.join('/Users/4ib/Desktop/git/cyclus_gui/neams/cyclus.sch')
            son_input_filepath = os.path.abspath(input_filepath)
            # add path to wasp2py.py to PYTHONPATH
            # Because setup_remote is installed in Workbench/rte, and wasp2py is installed in Workbench/wasppy
            # include the path from setup_remote to wasppy
            pathToSon2py= os.path.join(os.path.dirname(__file__),os.path.pardir,"wasppy")
            if not os.path.isdir(pathToSon2py):
                print ("***Error: Workbench Analysis Sequence Process (WASP) Python wrapper (WASPPY) is not in expected location: ",pathToSon2py)
            sys.path.append(pathToSon2py)
            # sys.path.append(os.path.join(os.path.expanduser("~"),"projects","wasp","wasppy"))
            import wasp2py # son2py
            # TODO: add a check to test the existence of the directory 'build/wasp/wasppy' 
            self.__input_dict = wasp2py.get_json_dict(schema_filepath,son_input_filepath)
        return self.__input_dict

    def run(self, options):
        """run the given executable"""	  
        pdir = os.path.join(os.path.dirname(os.path.abspath(__file__)))

        # check for cirrus libraries
        cirrus_path = os.path.abspath(os.path.join(pdir,'cirrus'))
        if not os.path.isdir(cirrus_path):
            self.echo(0,'The required Cirrus libraries are not in expected location: ' + cirrus_path)
            sys.exit(2)

        from cirrus.packages.base.util import Utils
        from cirrus.packages.base.config import ConfigBuilder, ConfigPacket, Configurator
        from cirrus.packages.base.const import ConfigConstants
        from cirrus.packages.base.passive_comm import PassiveCommFactory

        ### check input values
        self.__input_filepath = options.input
        self.echo(0,"Processing input file: " + self.__input_filepath)

        input_dict = self.get_dict_from_input_path(self.__input_filepath)
        
        #!version = self.get_version(self.__input_filepath)
        #!if version != "1.0.0":
        #!    raise ValueError("Invalid version_number specified in "+os.path.basename(self.__input_filepath)+": "+str(version))

        setup_properties = input_dict["setup_properties"]
        #! replace this with maybe a user argument
        self.hostname = setup_properties["hostname"]["value"]

        config_packet_builder = ConfigBuilder()
        config_packet_builder.set_follow_exe_with_input(False)
        config_packet_builder.set_cirrus_file_marker(str(RemoteConstants.SKIP_MARKER).strip())
        config_packet_builder.set_hostname(self.hostname)

        defaults_dict = {}

        if "localhost" == self.hostname:
            config_packet_builder.set_server_type("localhost")
            import getpass
            username = getpass.getuser()
            self._server_execution_dir = "/home/"+username
            config_packet_builder.set_username(username)
            config_packet_builder.set_client_type("localhost")
            # config for localhost case
            self._communication_type = "ssh"
            defaults_dict[Const.COMMUNICATION_TYPE] = self._communication_type      
            ssh_path = which('ssh')
            ssh_options = ""
            scp_path = which('cp') # TODO if "localhost" were to support Windows, woudl this need to be 'copy'?
            scp_options = '-pr'  
            defaults_dict[Const.SSH_PATH] = ssh_path
            defaults_dict[Const.SSH_OPTIONS] = ssh_options
            defaults_dict[Const.SCP_PATH] = scp_path
            defaults_dict[Const.SCP_OPTIONS] = scp_options               
        else:
            self.echo(0,"Attempting to enable communication with a remote runtime...")
            upload_pattern_dict = setup_properties["upload_patterns"]
            if upload_pattern_dict is not None and bool(upload_pattern_dict):
                self._upload_patterns = upload_pattern_dict["value"]
            download_pattern_dict = setup_properties["download_patterns"]
            if download_pattern_dict is not None and bool(download_pattern_dict):
                self._download_patterns = download_pattern_dict["value"]

            config_packet_builder.set_username(setup_properties["username"]["value"])
            autosearch = "true" # setup_properties["autosearch_rsa_keys"]
            config_packet_builder.set_look_for_private_keys(autosearch)

            # client-server communication setup
            self._communication_type = "ssh"
            if PassiveCommFactory.use_spur():
                self._communication_type = "spur"

            if "communication_type" in setup_properties:
                self._communication_type = setup_properties["communication_type"]["value"]
            if self._communication_type != "ssh" and self._communication_type != "spur":
                self.echo(0,'Invalid communication_type.  Must be "ssh" or "spur"')
                sys.exit(2)

            if self._communication_type == "ssh" or self._communication_type == "spur":
                config_packet_builder.set_server_type("passive")
                config_packet_builder.set_client_type("passive")
            
            defaults_dict[Const.COMMUNICATION_TYPE] = self._communication_type

            # load defaults for ssh & scp
            ssh_path = which('ssh')
            ssh_options = '-T'
            scp_path = which('scp')
            scp_options = '-pqr'

            if "ssh_specs" in setup_properties:
                # handle the ssh specs
                ssh_specs = setup_properties["ssh_specs"]
                if "ssh_options" in ssh_specs:
                    ssh_options = ssh_specs["ssh_options"]["value"]
                ssh_path = ssh_specs["ssh_path"]["value"]
                # if not os.path.isfile(ssh_path):
                #     raise ValueError("The specified path to 'ssh' is invalid")
                if "scp_options" in ssh_specs:
                    scp_options = ssh_specs["scp_options"]["value"]
                scp_path = ssh_specs["scp_path"]["value"]
                # if not os.path.isfile(scp_path):   
                #     raise ValueError("The specified path to 'scp' is invalid")             
         
            defaults_dict[Const.SSH_PATH] = ssh_path
            defaults_dict[Const.SSH_OPTIONS] = ssh_options
            defaults_dict[Const.SCP_PATH] = scp_path
            defaults_dict[Const.SCP_OPTIONS] = scp_options

            # config_packet_builder.set_automate_known_hosts(False) 
            # if "automate_known_hosts" in setup_properties:
            #     automate_known_hosts_dict = setup_properties["automate_known_hosts"]
            #     if automate_known_hosts_dict is not None and automate_known_hosts_dict["value"] == "true":
            #         config_packet_builder.set_automate_known_hosts(True) 

            self._server_execution_dir = setup_properties["remote_execution_home"]["value"]
        # end hostname != "localhost"

        if not self._server_execution_dir.endswith("/"):
            self._server_execution_dir = self._server_execution_dir + "/"

        self._deploy_to_server = True                       # TODO maybe expose this to the input.setup?

        self._override_existing_deployments = True          # TODO maybe expose this to the input.setup?
        if "scheduler_header" in setup_properties:
            self._header_lines = setup_properties["scheduler_header"]["value"]


        self._scheduler_type = setup_properties["scheduler_type"]["value"]

        # verify that the combo declared in the input is legal
        if self._scheduler_type == ConfigConstants.SCHEDULER_TYPE_VAL_PBS and "scheduler_specs" not in setup_properties:
            raise ValueError("The '"+ConfigConstants.SCHEDULER_TYPE_VAL_PBS+"' scheduler_type requires a 'scheduler_specs' entry")

        if self._scheduler_type == ConfigConstants.SCHEDULER_TYPE_VAL_SINGLE_BOX:
            if "scheduler_specs" in setup_properties:
                raise ValueError("The '"+ConfigConstants.SCHEDULER_TYPE_VAL_SINGLE_BOX+"' scheduler_type does not allow a 'scheduler_specs' entry")
            if "scheduler_cluster_specs" in setup_properties:
                raise ValueError("The '"+ConfigConstants.SCHEDULER_TYPE_VAL_SINGLE_BOX+"' scheduler_type does not allow a 'scheduler_cluster_specs' entry")

        if self._scheduler_type == ConfigConstants.SCHEDULER_TYPE_VAL_CLUSTER and "scheduler_cluster_specs" not in setup_properties:
            raise ValueError("The '"+ConfigConstants.SCHEDULER_TYPE_VAL_CLUSTER+"' scheduler_type requires a 'scheduler_cluster_specs' entry")

        # now we know it's legal... just set the values
        # handle the scheduler specs
        if "scheduler_specs" in setup_properties:
            scheduler_specs = setup_properties["scheduler_specs"]
            if scheduler_specs is not None and bool(scheduler_specs):
                # submit
                submit_path = scheduler_specs["submit_path"]["value"]
                submit_options = None
                if "submit_options" in scheduler_specs:
                    submit_options = scheduler_specs["submit_options"]["value"]
                # store submit defaults
                defaults_dict[Const.SUBMIT_PATH] = submit_path
                defaults_dict[Const.SUBMIT_OPTIONS] = submit_options

                # status
                status_path = scheduler_specs["status_path"]["value"]
                status_options = None
                if "status_options" in scheduler_specs:
                    status_options = scheduler_specs["status_options"]["value"]
                # store status defaults
                defaults_dict[Const.STATUS_PATH] = status_path
                defaults_dict[Const.STATUS_OPTIONS] = status_options

                # delete
                delete_path = scheduler_specs["delete_path"]["value"]
                delete_options = None
                if "delete_options" in scheduler_specs:
                    delete_options = scheduler_specs["delete_options"]["value"]
                # store delete defaults
                defaults_dict[Const.DELETE_PATH] = delete_path
                defaults_dict[Const.DELETE_OPTIONS] = delete_options                

                # hold
                hold_path = scheduler_specs["hold_path"]["value"]
                hold_options = None
                if "hold_options" in scheduler_specs:
                    hold_options = scheduler_specs["hold_options"]["value"]
                # store the hold defaults
                defaults_dict[Const.HOLD_PATH] = hold_path
                defaults_dict[Const.HOLD_OPTIONS] = hold_options

                # release
                release_path = scheduler_specs["release_path"]["value"]
                release_options = None
                if "release_options" in scheduler_specs:
                    release_options = scheduler_specs["release_options"]["value"]
                # store the release defaults
                defaults_dict[Const.RELEASE_PATH] = release_path
                defaults_dict[Const.RELEASE_OPTIONS] = release_options  

        # elif "scheduler_cluster_specs" in setup_properties:
        #     config_packet_builder.set_scheduler_type(ConfigConstants.SCHEDULER_TYPE_VAL_SINGLE_BOX)
        #     scheduler_specs = setup_properties["scheduler_cluster_specs"]
        #     if scheduler_specs is not None and bool(scheduler_specs):
        #         node_name = scheduler_specs["node_name"]["value"]
        #         if "" == node_name:
        #             raise ValueError("The node_name value is invalid")
        #         config_packet_builder.set_node_name(node_name)
        
        if 'tail_file' in setup_properties:
            tail_file_dict = setup_properties["tail_file"]
            if tail_file_dict is not None and bool(tail_file_dict):
                self._tail_file = tail_file_dict["value"]
                
        self._application_name = setup_properties["application_name"]["value"]
        self._remote_application_name = self.__sanitize_identifier(self._application_name)
        self._application_path = setup_properties["application_path"]["value"]
        self._runtime_command = setup_properties["runtime_command"]["value"]

        # the application name can be invented here
        application_name = self._application_name
        config_packet_builder.add_application(application_name, self._runtime_command)
        config_packet_builder.set_server_bin_python(self._runtime_command.split(" ")[0])

        son_input_filepath = os.path.abspath(self.__input_filepath)
        self._cfg_packet_filepath = son_input_filepath + ".json"
        config_packet_dict = config_packet_builder.get_config_packet()
        config_packet_dict[ConfigConstants.CLIENT_SECTION_KEY].update(defaults_dict)

        ### save to file
        Utils.save_dict_to_json(config_packet_dict, self._cfg_packet_filepath)
        self.echo(0,"Saved setup file to "+self._cfg_packet_filepath)
        
        from cirrus.packages.base.util import Utils
        from cirrus.packages.base.config import ConfigBuilder, ConfigPacket, Configurator
        
        config_packet_dict = Utils.load_dict_from_json_filepath(self._cfg_packet_filepath, ConfigPacket.__name__)
        username = None
        if "localhost" == self.hostname:
            import getpass
            username = getpass.getuser()
        self.hostname = config_packet_dict[ConfigConstants.CLIENT_SECTION_KEY][ConfigConstants.HOSTNAME_KEY]
        # check hostname is reachable
        # if not Utils.ping(hostname):
        #     self.echo(0,"Cannot communicate with server: " + hostname)        
        #     sys.exit(0)        
        # self.echo(0, "Successfully pinged "+hostname)

        _server_cirrus_root = Utils.get_cirrus_root_dir()
        if "localhost" != self.hostname:
            username = config_packet_dict[ConfigConstants.CLIENT_SECTION_KEY][ConfigConstants.USERNAME_KEY]
            _server_cirrus_root = AbstractRemoteRuntimeEnvironment.get_remote_runtime_storage_root(self._runtime_command) + "/cirrus/packages/"
        configurator = Configurator()
        interactive = False

        _cfg_result_filepath = configurator.process_config_packet(self._cfg_packet_filepath, _server_cirrus_root, self._application_name, username, self._server_execution_dir, self._deploy_to_server, self._override_existing_deployments, self._verify_connection, interactive)
        with open(_cfg_result_filepath) as f_:
            _cfg_result = json.load(f_)

        from cirrus.packages.base.util import Utils
        from cirrus.packages.base.config import ConfigBuilder, ConfigPacket, Configurator
        from cirrus.packages.client.job_client import JobClientFactory
        from cirrus.packages.base.const import ConfigConstants
        from cirrus.packages.base.passive_comm import PassiveCommFactory

        # verify the communication
        client_cfg = _cfg_result["main"][ConfigConstants.CLIENT_CFG_FILEPATH]
        # test the connection
        # if no RSA-Key in place, make one
        # if "generate_secure_key_pair" in setup_properties:
        #     generate_secure_key_pair_dict = setup_properties["generate_secure_key_pair"]
        #     if generate_secure_key_pair_dict is not None and generate_secure_key_pair_dict["value"] == "true":
        #         passive_comm = PassiveCommFactory.factory(client_cfg)
        #         self.echo(0,"Checking for a secure key pair... check for a password window")
        #         passive_comm.keyGenKeyFile()

        _verify = False
        _verbose = False
        job_client = JobClientFactory.factory(client_cfg, _verify, _verbose, defaults_dict) # not verifying the client

        if "localhost" != self.hostname:
            _verbose = True
            job_client.verify_communication(_verbose) # verifying the communication

            # if self._deploy_to_server:
            #     config_packet_dict = Utils.load_dict_from_json_filepath(self._cfg_packet_filepath, ConfigPacket.__name__)

            # deploy Cirrus setup to server
            configurator.deploy(_cfg_result_filepath, False, communication_type=self._communication_type)

        _verify = True
        _verbose = True
        job_client = JobClientFactory.factory(client_cfg, _verify, _verbose, defaults_dict) # now we are verifying the client

        if bool(self._header_lines):
            defaults_dict[Const.SCHEDULER_HEADER] = self._header_lines
        if self._upload_patterns is not None and bool(self._upload_patterns):
            defaults_dict[Const.UPLOAD_PATTERNS] = self._upload_patterns
        if self._download_patterns is not None and bool(self._download_patterns):
            defaults_dict[Const.DOWNLOAD_PATTERNS] = self._download_patterns
        if self._tail_file is not None and bool(self._tail_file):
            defaults_dict[Const.TAIL_FILE] = self._tail_file

        # TODO
        # job_client.verify_server()

        # create the new runtime
        classfile_filepath = self.__create_newclass_file()
        self.echo(0,"Completed writing the class file at " + classfile_filepath)

        # init the new remote runtime
        sys.path.append(self.rte_dir)
        new_class_name = self.__get_newclass_name()
        mod_name = os.path.basename(classfile_filepath).replace(".py","").replace(os.sep,".")

        # The runtime class was previously written, but could have already been loaded into memory
        # Check if a module reload is required
        if mod_name in sys.modules:
            self.echo(0,"Reloading ",mod_name," module...")
            module = reload(sys.modules[mod_name])   
        else:    
            self.echo(0,"Loading ",mod_name," module...")
            module = __import__(mod_name , fromlist = [new_class_name] )

        my_class = getattr(module, new_class_name)
        new_runtime = my_class()

        new_runtime.save_option_default_value_dict(defaults_dict)

        # call server to fetch local copies of options and grammar
        # options
        try:
            self.echo(0,"Attempting to download the options file")
            local_options_filepath = new_runtime._get_options_json_path(force=True, verbose=True)
            if os.path.isfile(local_options_filepath):
                self.echo(0,"Completed downloading the options file at " + local_options_filepath)
        except Exception as e:
            self.echo(0,"Failed to install the options: "+str(e))
        # # grammar
        # try:
        #     self.echo(0,"Attempting to download the grammar file")
        #     local_grammar_filepath = new_runtime._get_local_grammar_path(verbose=True)
        #     if os.path.isfile(local_grammar_filepath):
        #         self.echo(0,"Completed downloading the grammar file at " + local_grammar_filepath)
        # except Exception as e:
        #     self.echo(0,"Failed to install the grammar: "+str(e))

        self.cleanup = False

    def postrun(self, options):
        """actions to perform after the run finishes"""
        if self._tee_out is not None:
            self._tee_out.close()

    def run_args(self, options):
        """returns a list of arguments to pass to the given executable"""
        # build argument list
        args = [options.input]

        # always deploy_to_server
        args.append("--deploy_to_server")

        return args

    def __get_newclass_name(self):
        return self.__underscore_to_camelcase(self.__sanitize_identifier(self._application_name))

    def __underscore_to_camelcase(self, value):
        import string
        def camelcase(): 
            yield string.lower
            while True:
                yield string.capitalize

        c = camelcase()
        return "".join(c.next()(x) if x else '_' for x in value.split("_"))

    def __create_newclass_file(self):
        app_remote_resource_dir = get_rte_remote_resource_dir(self.rte_dir, self.__get_newclass_name())
        if os.path.isdir(app_remote_resource_dir):
            self.echo(0,"Removing existing application remote resources directory ",app_remote_resource_dir)
            shutil.rmtree(app_remote_resource_dir) 
        # we are using the application_name to create a class name
        new_class_name = self.__get_newclass_name()

        pmc = "" # pattern_methods_content
        # Include function for expanding patterns
        pmc += "    def expand_patterns(self, patterns):\n"
        pmc += "       if patterns is None or len(patterns) < 1:\n"
        pmc += "           return []\n"
        pmc += "       if isinstance(patterns,str):\n"
        pmc += "           patterns = [patterns]\n"
        pmc += "       from workbench import expand\n"
        pmc += "       replace_variables={\"BASENAME\":os.path.splitext(os.path.basename(self.input_file))[0]}\n"
        pmc += "       expanded = []\n"
        pmc += "       for pattern in patterns:\n"
        pmc += "           expanded.append(expand(pattern,replace_variables))\n"
        pmc += "       return expanded\n"

        content = ("#!/usr/bin/python\n" 
            "'''"+new_class_name+"'''\n" 
            "\n" 
            "import sys,os\n" 
            "from util.abstract_remote import "+AbstractRemoteRuntimeEnvironment.__name__ + "\n" 
            "\n" 
            "class "+new_class_name+"("+AbstractRemoteRuntimeEnvironment.__name__ + "):\n" 
            "\n" 
            "    def __init__(self):\n" 
            "        super("+AbstractRemoteRuntimeEnvironment.__name__ + ", self).__init__()\n" 
            "\n" 
            "    def app_name(self):\n" 
            "        ### helps the user distinguish between runtimes\n" 
            "        return '"+self._application_name+"'\n" 
            "\n" 
            "    def get_remote_runtime_command(self):\n" 
            "        ### this value should be a key in the server.cfg file that indicates a value like:\n"
            "        #           /home/username/workbench/rte/entry.sh /home/username/workbench/rte/hello_world.py\n"
            "        return '"+self._runtime_command+"'\n" 
            "\n" 
            "    def _get_remote_application_path(self):\n" 
            "        return '"+self._application_path+"'\n" 
            "\n" 
            "    def _get_scheduler_type(self):\n" 
            "        return '"+self._scheduler_type+"'\n"  
            "\n" 
            "    def _get_communication_type(self):\n" 
            "        return '"+self._communication_type+"'\n"  
            "\n" 
            "\n" + pmc + "\n"
            "if __name__ == '__main__':\n"
            "    from util.check_version import CheckVersion\n"
            "    CheckVersion.check()\n" 
            "    import signal\n" 
            "    rte = "+new_class_name+"()\n" 
            "    signal.signal(signal.SIGTERM, rte.exit_gracefully)\n" 
            "    signal.signal(signal.SIGINT, rte.exit_gracefully)\n" 
            "    # execute runtime, ignoring first argument (the python script itself)\n" 
            "    rte.remote_execute(sys.argv[1:])\n" 
            "\n")

        pdir = os.path.abspath(os.path.dirname(__file__))
        new_name = self.__sanitize_identifier(self._application_name) + ".py"
        filepath = os.path.join(pdir, new_name)
        # in case the remote name would override one of the deployed classes...
        from util.util import Utilities
        if os.path.isfile(filepath) and not Utilities.is_remote_runtime_file(filepath):
            msg = "*** ERROR: The file name " + new_name + " is used for one of the standard deployed runtimes.  You must chose another value for 'application_name'"
            if self.__input_filepath is not None:
                msg = msg + " in the file " + str(self.__input_filepath)
            self.echo(0,msg)
            sys.exit(1)
        with open(filepath,"w") as f:
            f.write(content)
        return filepath

    def __gen_valid_identifier(self, seq):
        # get an iterator
        itr = iter(seq)
        # pull characters until we get a legal one for first in identifer
        for ch in itr:
            if ch == '_' or ch.isalpha():
                yield ch
                break
        # pull remaining characters and yield legal ones for identifier
        for ch in itr:
            if ch == '_' or ch.isalpha() or ch.isdigit():
               yield ch

    def __sanitize_identifier(self, name):
        return ''.join(self.__gen_valid_identifier(name))

if __name__ == "__main__":
    # execute runtime, ignoring first argument (the python script itself)
    from util.check_version import CheckVersion
    CheckVersion.check()
    args = sys.argv[1:]
    python = sys.executable
    args.insert(0,python)
    args.insert(0,"-e")
    rte = SetupRemoteRuntimeEnvironment()
    rte.execute(args)
