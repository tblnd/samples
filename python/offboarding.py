# Module to audit the offboarding process of multiple online services
from __future__ import print_function

import argparse
import json
import os
import pickle
import platform
import re
import subprocess
from datetime import date, datetime

import requests
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from onepass import OnePass

Constant
OP = OnePass(session_token=os.getenv('OP_TOKEN'))
OSPLATFORM = platform.system()


def date_converter(date, format):
    datetimeObj = datetime.strptime(date, format)
    return datetimeObj


def title(name):
    print('{:_^50}'.format(''))
    print('{:^50}'.format(name))
    print('{:_^50}'.format(''))


class Offboarded:

    def __init__(self, startDate, endDate):
        self.startDate = startDate
        self.endDate = endDate

    # Date validation
    def date_validation(self):

        dateStart = date_converter(self.startDate + 'T00:00:00Z', '%Y%m%dT%H:%M:%SZ')

        if dateStart.date() < date(year=2020, month=1, day=1):
            print('Earliest date possible is 2020-01-01')
            quit()

        if dateStart.date() > date.today():
            print('The future is unpredictable')
            quit()

        if self.endDate:
            dateEnd = date_converter(self.endDate + 'T00:00:00Z', '%Y%m%dT%H:%M:%SZ')

            if dateStart.date() > dateEnd.date():
                print('Time period error')
                quit()

            if dateEnd.date() > date.today():
                print('End date error')
                quit()

    # Print date information
    def header(self):

        dateStart = date_converter(self.startDate + 'T00:00:00Z', '%Y%m%dT%H:%M:%SZ')
        print(f'\nAudit performed on {date.today()}')

        if self.endDate:
            dateEnd = date_converter(self.endDate + 'T00:00:00Z', '%Y%m%dT%H:%M:%SZ')
            print(f'\nFrom {dateStart:%Y-%m-%d} to {dateEnd:%Y-%m-%d}')
            print('{:_^50}'.format(''), end='\n')
        else:
            print(f'\nFrom {dateStart:%Y-%m-%d} to {date.today()}')
            print('{:_^50}'.format(''), end='\n')

    # Source of truth
    def github_offboarding(self):

        def offboarding_list(string, dictionary, date, number):
            try:
                email = re.search('([a-z]{1,30}|\.){1,7}@(DOMAIN.com)', str(string))
                dictionary.update({email.group(): date})
            except:
                print('No email found in issue #' + str(number))

        def date_converter(date, format):
            datetimeObj = datetime.strptime(date, format)
            return datetimeObj

        dateStart = date_converter(self.startDate + 'T00:00:00Z', '%Y%m%dT%H:%M:%SZ')
        githubToken = OP.get_note('githubToken')
        owner = 'ORGANISATION'
        repo = 'infrastructure'
        url = f'https://api.github.com/repos/{owner}/{repo}/issues'
        githubHeaders = {'Accept': 'application/vnd.github.v3+json', 'Authorization': f'token {githubToken}'}
        response = requests.request('GET', url, headers=githubHeaders, params={'state': 'closed',
                                                                               'labels': 'offboarding',
                                                                               'since': f'{dateStart:%Y-%m-%d}T00:00:00Z',
                                                                               'per_page': 100}).json()
        if not response:
            print('No employee offboarded in the specified date')
            exit()

        offboardedList = {}
        for issue in response:
            if 'pull_request' in issue:
                pass
            else:
                createdDate = date_converter(issue['created_at'], '%Y-%m-%dT%H:%M:%SZ')
                closedDate = date_converter(issue['closed_at'], '%Y-%m-%dT%H:%M:%SZ')

                if self.endDate:
                    dateEnd = date_converter(self.endDate + 'T00:00:00Z', '%Y%m%dT%H:%M:%SZ')
                    if dateStart.date() <= closedDate.date() <= dateEnd.date():
                        offboarding_list(issue['body'], offboardedList, issue['closed_at'], issue['number'])
                else:
                    if dateStart.date() <= closedDate.date():
                        offboarding_list(issue['body'], offboardedList, issue['closed_at'], issue['number'])

        return offboardedList

    # Print offboarded employees
    def print_offboarding(self, dictionary):

        print('\nEmployees offboarded (' + str(len(dictionary.keys())) + ') {:<2} Issue closing date'.format(' '), end='\n\n')

        for employee in dictionary.keys():
            date = date_converter(dictionary[employee], '%Y-%m-%dT%H:%M:%SZ')
            print(employee + f'\t\t{date:%Y-%m-%d}')

        return dictionary


class CMDB:

    def __init__(self, dict):
        self.dict = dict

    # CMDB account status lookup
    def account_status(self):

        infraActive = {}
        for employee in self.dict.keys():
            name = employee.replace('@DOMAIN.com', '')
            audit = subprocess.run(['ack', '--match',  '^' + name + '$|' + employee, os.getenv('HOME')+'/COMPANY/infrastructure'], stdout=subprocess.PIPE)

            if not audit.stdout.decode('utf-8'):
                pass
            else:
                filesLines = subprocess.run(['cut', '-d', ':', '-f', '1-2'], stdout=subprocess.PIPE, input=audit.stdout).stdout.decode('utf-8')
                infraActive.update({name: filesLines})

        return infraActive

    # Print CMDB account status
    def print_status(self, dictionary):

        if not dictionary:
            title('Infrastructure')
            print('\nNo access remaining\n')
        else:
            title('Infrastructure')
            for finding in dictionary.keys():
                print("'" + finding + "' found in:\n")
                print(dictionary[finding])


class GoogleOrg:

    def __init__(self, dict):
        self.dict = dict

    # Google account status lookup
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

        # Google lookup
        directory = build('admin', 'directory_v1', credentials=creds)
        googleActive = {}
        googleSuspended = []
        googleDeleted = []

        for employee in self.dict.keys():
            try:
                result = directory.users().get(userKey=employee).execute()
                if result['suspended'] == False:
                    googleActive.update({employee: result['lastLoginTime']})
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

    # Print Google account status
    def print_status(self, tulpe):

        title('Google' + ' (' + str(len(tulpe[0]) + len(tulpe[1]) + len(tulpe[2])) + ')')
        print('\n- Active account(s) (' + str(len(tulpe[0].keys())) + ')' + ': last login')
        for employee in tulpe[0].keys():
            lastLogin = date_converter(tulpe[0][employee], '%Y-%m-%dT%H:%M:%S.%fZ')
            print(employee + ': ' + f"{lastLogin:%Y-%m-%d}")

        print('\n- Suspended account(s) (' + str(len(tulpe[1])) + ')')
        for employee in tulpe[1]:
            print(employee)

        if tulpe[2]:
            print('\n- Deleted account(s) (' + str(len(tulpe[2])) + ')')
            for employee in tulpe[2]:
                print(employee)


class SlackOrg:

    def __init__(self, dict):
        self.dict = dict

    # Slack account status lookup
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

    # Print Slack account status
    def print_status(self, tulpe):

        title('Slack' + ' (' + str(len(tulpe[0]) + len(tulpe[1])) + ')')
        print('\n- Active account(s) (' + str(len(tulpe[0])) + ')')
        for employee in tulpe[0]:
            print(employee)

        print('\n- Deleted account(s) (' + str(len(tulpe[1])) + ')')
        for employee in tulpe[1]:
            print(employee)


class KolideOrg:

    def __init__(self, dict):
        self.dict = dict

    # Kolide account status lookup
    def account_status(self):

        kolideToken = OP.get_note('kolideToken')
        kolideActive = []
        kolideArchived = []
        kolideDeleted = []

        for employee in self.dict.keys():
            url = 'https://k2.kolide.com/api/v0/people'
            slackHeaders = {'Accept': 'application/json', 'Authorization': f'Bearer {kolideToken}'}
            response = requests.request('GET', url, headers=slackHeaders, params={'search': employee}).json()

            if response['data']:
                for profile in response['data']:

                    if profile['status'] == 'Active':
                        kolideActive.append(profile['email'])

                    if profile['status'] == 'Archived':
                        kolideArchived.append(profile['email'])
            else:
                kolideDeleted.append(employee)

        return kolideActive, kolideArchived, kolideDeleted

    # Print Kolide account status
    def print_status(self, tulpe):

        title('Kolide' + ' (' + str(len(tulpe[0]) + len(tulpe[1]) + len(tulpe[2])) + ')')
        print('\n- Active profile(s) (' + str(len(tulpe[0])) + ')')
        for employee in tulpe[0]:
            print(employee)

        print('\n- Archived profile(s) (' + str(len(tulpe[1])) + ')')
        for employee in tulpe[1]:
            print(employee)

        if tulpe[2]:
            print('\n- Deleted profile(s) (' + str(len(tulpe[2])) + ')')
            for employee in tulpe[2]:
                print(employee)


class OnePasswordOrg:

    def __init__(self, dict):
        self.dict = dict

    # 1Password account status lookup
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

    # Print 1Password account status
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


# Instantiate argument parser
def get_args():

    accounts = argparse.ArgumentParser(prog='offboarding',
                                       usage='%(prog)s --startDate YYYYMMDD | --endDate YYYYMMDD',
                                       description="""offboarding is a Python 3 script that interacts with the ORGANISATION infrastructure repository
                                               as well as Google, Slack, Kolide and 1Password to lookup up the account status of employees.
                                               By default, the script uses a list of employees created from the closed offboarding labelled
                                               issues of the infrastructure repository as source of truth and queries all services.""")
    accounts.version = '2.0'

    accounts.add_argument('-s', '--startDate', action='store', type=str, help='start data of the audit period formated as YYYYMMDD')
    accounts.add_argument('-e', '--endDate', action='store', type=str, required=False, help='end date of the audit period formated as YYYYMMDD', metavar='')

    return accounts.parse_args()


# Run program
def main(args):

    if not os.path.exists('/usr/bin/ack') and not os.path.exists('/usr/local/bin/ack'):
        print("offboarding.py requires the tool 'ack'. Download it from your package manager and retry this script.")

    offboarding = Offboarded(args.startDate, args.endDate)
    offboarding.date_validation()
    departures = offboarding.github_offboarding()

    cmdb = CMDB(departures)
    google = GoogleOrg(departures)
    slack = SlackOrg(departures)
    kolide = KolideOrg(departures)
    onepass = OnePasswordOrg(departures)

    offboarding.header()
    offboarding.print_offboarding(departures)
    cmdb.print_status(cmdb.account_status())
    google.print_status(google.account_status())
    slack.print_status(slack.account_status())
    kolide.print_status(kolide.account_status())
    onepass.print_status(onepass.account_status())


if __name__ == '__main__':
    args = get_args()
    main(args)
