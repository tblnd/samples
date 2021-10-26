# 1Password CLI python3 wrapper

import json
import os
from getpass import getpass
from subprocess import run

# Constants
OP_CLI = "op"
USERNAME = 0
PASSWORD = 1


class OnePass:

    def __init__(self, session_token=None):
        # Set the session token
        if session_token is None:
            session_token = getpass("Enter your 1Password CLI Session Token: ")
        self.__session_token = session_token

    @staticmethod
    def __run_command(command, text=True, json_output=True):
        # Run the command
        result = run(
            command,
            text=text,
            capture_output=True
        )

        # Return the output
        if json_output:
            return json.loads(result.stdout)
        else:
            return result.stdout

    # Custom method
    @staticmethod
    def __run_command_file(command):
        # Run the command
        result = run(
            command,
            capture_output=True
        )

        # Return bytes
        return result

    def __create_basic_command(self, details):
        # Create a basic op command to run
        result = [OP_CLI]
        result.extend(details.split(" "))
        result.append("--session=" + self.__session_token)
        return result

    def __run_op_command(self, command_as_str, text=True, json_output=True):
        # Given a string, simply run a op command
        return self.__run_command(
            self.__create_basic_command(
                command_as_str
            ),
            text=text,
            json_output=json_output
        )

    # Custom method
    def __run_op_command_file(self, command_as_str):
        # Given a string, simply run a op command
        return self.__run_command_file(
            self.__create_basic_command(
                command_as_str
            )
        )

    def get_credentials(self, item_name):
        # Get credentials for a specific item
        result = {}
        output = self.__run_op_command("get item {}".format(item_name))

        result["username"] = str(
            output["details"]["fields"][USERNAME]["value"]
        )

        result["password"] = str(
            output["details"]["fields"][PASSWORD]["value"]
        )
        return result

    # Custom method
    def get_password(self, item_name):
        # Get the password of a specific item
        output = self.__run_op_command("get item {}".format(item_name))
        result = str(
            output["details"]['password']
        )
        return result

    def get_totp(self, item_name):
        # Get the One-Time-Password for a specifc item
        return self.__run_op_command("get totp {}".format(item_name))

    def get_uuid(self, file_name):
        # Get the UUID of a specific item
        output = self.__run_op_command("get item {}".format(file_name))
        return output["uuid"]

    # Custom method
    def get_note(self, item_name):
        # Get note content of a specific item
        output = self.__run_op_command("get item {}".format(item_name))
        result = str(
            output["details"]['notesPlain']
        )
        return result

    # Custom method
    def add_file(self, file_name):
        # Add a file in the private vault. Item has the same name has the file.
        result = self.__run_op_command("create document {}".format(file_name))

    # Custom method
    def copy_file(self, file_name):
        # Copy file in your working directory.
        result = self.__run_op_command_file("get document {} --output {}".format(file_name, file_name))

        if os.stat(file_name).st_size == 0:
            os.remove(file_name)
        else:
            return result

    # Custom method
    def create_file(self, item_name, file_name):
        # Create file in the working directory.
        output = self.__run_op_command("get item {}".format(item_name))
        data = output["details"]['notesPlain']

        with open(file_name, 'w') as file:
            file.write(data)
            file.close()
        return file

    def save_file(self, file_name, save_location):
        # Save the file to a location
        output = self.__run_op_command("get document {}".format(self.get_uuid(file_name)),
                                       text=False,
                                       json_output=False)

        with open(save_location, "wb") as file:
            file.write(output)

        print("File saved to: " + str(save_location))

    # Custom method
    def get_user(self, user):
        # Get the details of a user
        output = self.__run_op_command("get user {}".format(user))
        return output
