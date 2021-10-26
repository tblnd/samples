# Module to lookup the user accounts status of multiple online services
from __future__ import print_function

import argparse
import json
import os
import pickle

import requests
import yaml
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from onepass import OnePass

# Constant
OP = OnePass(session_token=os.getenv('OP_TOKEN'))


def title(name):
    print('{:_^50}'.format(''))
    print('{:^50}'.format(name))
    print('{:_^50}'.format(''))


class GoogleAccount:

    def __init__(self, dict):
        self.dict = dict

    # Google user account status lookup
    def account_status(self):

        # Google OAuth authentication flow
        scopes = ['https://www.googleapis.com/auth/admin.directory.user.readonly',
                  'https://www.googleapis.com/auth/admin.directory.user.alias.readonly']

        creds = None
        OP.copy_file('token.pickle')

        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                credentials = OP.create_file('googleCredentials', 'credentials.json')
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', scopes)
                creds = flow.run_local_server(port=0)

                pickle.dump(creds, open('token.pickle', 'wb'))
                OP.add_file('token.pickle')

        # Google user lookup account status lookup
        directory = build('admin', 'directory_v1', credentials=creds)
        googleActive = []
        googleSuspended = []
        googleDeleted = []

        for employee in self.dict.keys():
            try:
                result = directory.users().get(userKey=employee).execute()
                if result['suspended'] == False:
                    googleActive.append(employee)
                else:
                    googleSuspended.append(employee)
            except:
                googleDeleted.append(employee)
        try:
            os.remove('token.pickle')
            os.remove('credentials.json')
        except Exception:
            pass

        return googleActive, googleSuspended, googleDeleted

    # Print Google user accounts status
    def print_status(self, tulpe):

        title('Google' + ' (' + str(len(tulpe[0]) + len(tulpe[1]) + len(tulpe[2])) + ')')
        print('\n- Active account(s) (' + str(len(tulpe[0])) + ')')
        for employee in tulpe[0]:
            print(employee)

        print('\n- Suspended account(s) (' + str(len(tulpe[1])) + ')')
        for employee in tulpe[1]:
            print(employee)

        if tulpe[2]:
            print('\n- Deleted account(s) (' + str(len(tulpe[2])) + ')')
            for employee in tulpe[2]:
                print(employee)


class SlackAccount:

    def __init__(self, dict):
        self.dict = dict

    # Slack user account status lookup
    def account_status(self):

        slackToken = OP.get_note('slackToken')
        slackActive = []
        slackDeleted = []

        for employee in self.dict.keys():
            url = 'https://slack.com/api/users.lookupByEmail'
            slackHeaders = {'Accept': 'application/x-www-form-urlencoded'}
            response = requests.request('GET', url, headers=slackHeaders, params={'token': slackToken, 'email': employee}).json()

            if response['ok'] == True:
                slackActive.append(employee)

            else:
                slackDeleted.append(employee)

        return slackActive, slackDeleted

    # Print Slack user account status
    def print_status(self, tulpe):

        title('Slack' + ' (' + str(len(tulpe[0]) + len(tulpe[1])) + ')')
        print('\n- Active account(s) (' + str(len(tulpe[0])) + ')')
        for employee in tulpe[0]:
            print(employee)

        print('\n- Deleted account(s) (' + str(len(tulpe[1])) + ')')
        for employee in tulpe[1]:
            print(employee)


class OnePasswordAccount:

    def __init__(self, dict):
        self.dict = dict

    # 1Password user account status lookup
    def account_status(self):

        onepassActive = []
        onepassSuspended = []
        onepassDeleted = []

        for employee in self.dict.keys():
            try:
                account = OP.get_user(employee)

                if account['state'] == 'A':
                    onepassActive.append(employee)

                if account['state'] == 'S':
                    onepassSuspended.append(employee)
            except:
                onepassDeleted.append(employee)

        return onepassActive, onepassSuspended, onepassDeleted

    # Print 1Password user account status
    def print_status(self, tulpe):

        title('1Password' + ' (' + str(len(tulpe[0]) + len(tulpe[1]) + len(tulpe[2])) + ')')
        print('\n- Active account(s) (' + str(len(tulpe[0])) + ')')
        for employee in tulpe[0]:
            print(employee)

        print('\n- Suspended account(s) (' + str(len(tulpe[1])) + ')')
        for employee in tulpe[1]:
            print(employee)

        print('\n- Deleted account(s) (' + str(len(tulpe[2])) + ')')
        for employee in tulpe[2]:
            print(employee)


class CLI:
    # Options for argument parser
    def __init__(self, google, slack, onepass):
        self.google = google
        self.slack = slack
        self.onepass = onepass


# Instantiate argument parser
def get_args():
    accounts = argparse.ArgumentParser(prog='iamstatus',
                                       usage='%(prog)s -f [yaml file] --google --slack --onepass',
                                       description='iamstatus is a Python 3 module that interacts with Google, Slack and 1Password APIs to lookup up user accounts status.')
    accounts.version = '1.0'
    accounts.add_argument('-f', '--file', action='store', metavar='file', help='user accounts file')
    accounts.add_argument('-g', '--google', action='store_true', required=False, help='Google account status')
    accounts.add_argument('-s', '--slack', action='store_true', required=False, help='Slack account status')
    accounts.add_argument('-o', '--onepass', action='store_true', required=False, help='1Password account status')

    return accounts.parse_args()


def main(args):

    iamstatusCLI = CLI(args.google, args.slack, args.onepass)

    with open(args.file) as yamlFile:
        userDict = yaml.load(yamlFile, Loader=yaml.FullLoader)

        if args.google:
            googleData = GoogleAccount(userDict)
            googleData.print_status(googleData.account_status())

        if args.slack:
            slackData = SlackAccount(userDict)
            slackData.print_status(slackData.account_status())

        if args.onepass:
            onepassData = OnePasswordAccount(userDict)
            onepassData.print_status(onepassData.account_status())


if __name__ == '__main__':
    args = get_args()
    main(args)
