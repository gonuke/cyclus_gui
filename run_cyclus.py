import paramiko
import uuid
import os

class cyclus_run:
    def __init__(self, input_path, output_path):
        # microsoft azure accoutn
        ip = '40.121.41.236'
        self.username = 'user1'
        try:
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(ip, username=self.username,
                         password=' ')
        except Exception as e:
            self.err_message = """Did not connect! Check Internet connection or contact baej@ornl.gov
            If you are using this in a secure network, that might be the reason as well.
            Error message:""" + e
            print(self.err_message)
            self.return_code = -1
        self.upload_run_download(input_path, output_path)
        self.return_code = 0


    def run_and_print(self, command, p=False):
        if p:
            print('Running command:\n%s' %command)
            print('============================')
        i, o, e = self.ssh.exec_command(command)
        output = '\n'.join(o.readlines())
        error = '\n'.join(e.readlines())
        if len(error) != 0:
            if p:
                print('Error:')
                print(error)
                print('\n\n')
            return error
        if p:
            print('Output:')
            print(output)
            print('============================')
            print('Finish\n')
        return 0

    def upload_run_download(self, input_path, output_path):
        ftp = self.ssh.open_sftp()
        # upload yo

        rnd_dir = '/home/%s/%s' %(self.username, str(uuid.uuid4()))
        remote_input_path = os.path.join(rnd_dir, 'input.xml')

        # make temporary directory with random hash so no overlap
        # during simultaneous run
        if self.run_and_print('mkdir %s' %rnd_dir) != 0:
            raise ValueError('That hash file already exists..')
        # upload generated input file
        ftp.put(input_path, remote_input_path)
        
        # run Cyclus
        remote_output_path = remote_input_path.replace('input.xml',
                                                       'output.sqlite')
        c = self.run_and_print('/home/baej/.local/bin/cyclus %s -o %s --warn-limit 0' %(remote_input_path,
                                                                         remote_output_path), p=True)
        if c == 0 or ('error' not in c and 'Abort' not in c and 'fatal' not in c):
            # download yo
            ftp.get(remote_output_path, output_path)

            # delete file
            self.run_and_print('rm -rf %s' %rnd_dir)
        else:
            self.err_message = 'Cyclus run failed! Check terminal output'
            print(self.err_message)
            self.return_code = -2


