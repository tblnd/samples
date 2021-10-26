# Module to audit SSH access on a specific host based on an external source of truth
import json
import os
import re

import paramiko
from onepass import OnePass

# Constants
SESSION = OnePass(session_token=os.environ['OP_TOKEN'])
SSH = SESSION.get_password('SSH')


class MySSHClient:

    # Create a SSH client
    def __init__(self, hostname, username, privateKeyFilename, password):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.connect(hostname, username=username, key_filename=privateKeyFilename, password=password)

    # Run arbitrary command on remote host
    def command(self, command):
        self.stdin, self.stdout, self.stderr = self.client.exec_command(command, get_pty=True)
        users = self.stdout.read().decode('utf-8')
        return users

    # Format the command's stdout items in a user list without domain(s)
    def stdout_list(self, output):
        usersList = []
        for result in output.strip().split():
            username = re.sub('@[a-z]{1,20}\.[a-z]{1,10}', '', result)
            usersList.append(username)
        del self.stdin, self.stdout, self.stderr
        return usersList

    def closeConnection(self):
        if(self.client != None):
            self.client.close()


#  Function
def report(title, data):
    print('{:_^45}'.format(''))
    print('{:^45}'.format(title))
    print('{:_^45}'.format(''))
    print(json.dumps(data, indent=4))


# External source of truth
host = {'users': ['user1', 'user2', 'user7'],
        'roles': {'role1': {'id': ['user1', 'user3'],
                            'home': '/var/lib/role1'},
                  'role2': {'id': ['user2', 'user3', 'user4']}}}

report('Source of truth', host)

# Instantiation
authkeys = MySSHClient('IP address', 'username', 'pathToPrivateKey', SSH)   # update the IP address, username and pathToPrivateKey
sourceTruthOnly = {'users': [], 'roles': []}
hostUsersOnly = {'users': authkeys.stdout_list(authkeys.command('ls /home')), 'roles': {}}

# Search remote host for users under /home
for user in host['users']:
    userOutput = authkeys.command('grep -E "([a-z]{1,30}|\.){1,7}" /home/%s/.ssh/authorized_keys | cut -d" " -f3' % user)

    if 'No such file or directory' in userOutput:
        sourceTruthOnly['users'].append(user)

    else:
        hostUsersOnly['users'].remove(user)

# Search remote host for role users
for role, roleData in host['roles'].items():

    # Search remote host for role users under /home
    if not 'home' in roleData:
        roleOutput = authkeys.command('grep -E "([a-z]{1,30}|\.){1,7}" /home/%s/.ssh/authorized_keys | cut -d" " -f3' % role)

        if 'No such file or directory' in roleOutput:
            sourceTruthOnly['roles'].append(role)

        else:
            hostUsersOnly['users'].remove(role)
            hostUsersOnly['roles'].update({role: []})
            serverAccess = authkeys.stdout_list(roleOutput)

            for user in serverAccess:

                if not user in roleData['id']:
                    hostUsersOnly['roles'][role].append(user)
                else:
                    pass

    # Search remote host for role users with a custom $HOME
    if 'home' in roleData:
        home = roleData['home']
        roleHomeOutput = authkeys.command('grep -E "([a-z]{1,30}|\.){1,7}" %s/.ssh/authorized_keys | cut -d" " -f3' % home)

        if 'No such file or directory' in roleHomeOutput:
            sourceTruthOnly.append(user)

        else:
            hostUsersOnly['roles'].update({role: []})
            serverAccess = authkeys.stdout_list(roleHomeOutput)

            for user in serverAccess:

                if not user in roleData['id']:
                    hostUsersOnly['roles'][role].append(user)
                else:
                    pass

authkeys.closeConnection()

# Print report
report('Users only included in the source of truth', sourceTruthOnly)
report('Users only seen on remote host', hostUsersOnly)
