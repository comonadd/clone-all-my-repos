#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import base64

from github import Github

class AuthData(object):

    AUTH_DATA_DELIM_CH = ','

    def __init__(self, username=None, password=None, token=None):
        self.username = username if (len(username) > 0) else None
        self.password = password if len(password) > 0 else None
        self.token = token if len(token) > 0 else None

    def is_token(self):
        return not (self.token == None)

    def encode_raw(self):
        return '{}{}{}{}{}'.format(
            self.token or '',
            AuthData.AUTH_DATA_DELIM_CH,
            self.username or '',
            AuthData.AUTH_DATA_DELIM_CH,
            self.password or '',
            AuthData.AUTH_DATA_DELIM_CH,
        )

    def encode(self):
        a = self.encode_raw().encode('utf-8')
        res = base64.b64encode(a)
        print(a)
        print(res)
        return res

    @staticmethod
    def decode_raw(raw):
        if len(raw) <= 0: return None
        print(raw)
        data = raw.split(AuthData.AUTH_DATA_DELIM_CH)
        return AuthData(token=data[0], username=data[1], password=data[2])

    @staticmethod
    def decode(raw):
        return AuthData.decode_raw(base64.b64decode(raw.encode('utf-8')).decode())

def ask(question):
    res = False
    repeat = True
    while repeat:
        repeat = False
        res_s = input('{} (\"y/yes\" if yes, \"n/no\" if no): '.format(question))
        if res_s.lower() in ['y', 'yes']:
            res = True
        elif res_s.lower() in ['n', 'no']:
            res = False
        else:
            repeat = True
    return res

class Application(object):

    HOME_DIR_AUTH_DATA_FILE_NAME = '.clone-all-my-repos-github-auth-data'

    def construct_auth_data_file_path(self):
        home = os.getenv("HOME")
        return '{}/{}'.format(home, self.HOME_DIR_AUTH_DATA_FILE_NAME)

    def get_auth_data(self):
        file_path = self.construct_auth_data_file_path()
        if not os.path.exists(file_path): return None
        with open(file_path, 'r') as f:
            raw_data = f.read()
            return AuthData.decode(raw_data)

    def save_auth_data(self, auth_data):
        file_path = self.construct_auth_data_file_path()
        data_to_write = auth_data.encode()
        with open(file_path, 'w') as f:
            f.write(data_to_write.decode())
            return True

    def ask_for_auth_data(self):
        # Ask if 2FA is enabled
        repeat = True
        is_2fauth_enabled = ask('Does your GitHub account have 2-Factor Authentication enabled?')
        if is_2fauth_enabled:
            token = input('Enter personal access token for repository management: ')
            return AuthData(token=token)
        else:
            username = input('Enter GitHub username: ')
            password = input('Enter GitHub password: ')
            return AuthData(username=username, password=password)

    def authorize(self):
        # Ask for authentication data
        want_to_use_saved = ask('Do you want to use saved authentication data?')
        auth_data = None
        if want_to_use_saved:
            auth_data = self.get_auth_data()
            if not auth_data:
                print('You don\'t have any authentication data saved locally')
                auth_data = self.ask_for_auth_data()
                self.save_auth_data(auth_data)
        else:
            auth_data = self.ask_for_auth_data()
            self.save_auth_data(auth_data)
        # Create API handler instance
        if auth_data.is_token():
            return Github(auth_data.token)
        else:
            return Github(auth_data.username, auth_data.password)

    def run(self):
        g = self.authorize()
        cloned_repos_dir = input('Enter directory path to clone repositories to (leave empty if current): ')
        if len(cloned_repos_dir) <= 0:
            cloned_repos_dir = os.getcwd()
        for repo in g.get_user().get_repos():
            clone_url = repo.ssh_url
            os.system('git clone {} {}'.format(clone_url,
                                               '{}/{}'.format(cloned_repos_dir,
                                                             repo.name)))

    def __init__(self):
        pass

def main():
    app = Application()
    app.run()

if __name__ == '__main__':
    main()
