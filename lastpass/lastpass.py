"""
API for LastPass CLI (lpass)

Prerequisites:
  * Install lastpass-cli: https://github.com/lastpass/lastpass-cli
"""
import os
import subprocess
import re
import json
from .exceptions import *


class Vault():

    LPASS_STATUS_REGEX = r"Logged in as (?P<user>[^\s]*)\.$"
    LPASS_ID_REGEX = r" \[id: (?P<id>\d+)\]$"
    LPASS_MAIN_COMMAND = "lpass"
    LPASS_DISABLE_PINENTRY = "LPASS_DISABLE_PINENTRY"
    PINENTRY_DISABLED = "1"

    def __init__(self, username):
        self._username = username
        self._setup()

    ##
    # Private methods
    ##

    def _setup(self):
        self._env = os.environ.copy()
        self._env[self.LPASS_DISABLE_PINENTRY] = self.PINENTRY_DISABLED
        self._stdout = subprocess.PIPE

    def _run_piped(self, piped_command, main_command, stdout=None):
        piped_proc = self._run_command(piped_command)
        main_proc = self._run_command(main_command, stdout=stdout, stdin=piped_proc.stdout)

        output = main_proc.communicate()

        return output, main_proc.returncode

    def _run_command(self, args_list, stdout=None, stdin=None):
        if not stdout:
            stdout = self._stdout
        return subprocess.Popen(args_list, env=self._env, stdout=stdout, stdin=stdin)

    ##
    # Properties
    ##

    @property
    def username(self):
        return self._username

    ##
    # Public methods
    ##

    def login(self, password, otp=None):
        secrets = password
        if otp:
            secrets += fr"\n{otp}"

        secrets_command = ["printf", secrets]
        login_command = [self.LPASS_MAIN_COMMAND, "login", self.username, "--trust"]

        _, code = self._run_piped(secrets_command, login_command, stdout=subprocess.DEVNULL)

        if code != 0:
            raise WrongCredentialsException("Invalid username, password or OTP code.")

    def add_note(self, note_type, note, name):
        """
        lpass add --note-type=NOTETYPE --non-interactive --sync=now NAME

        params:
            note_type: str (lastpass.types), LastPass note type.
            note: str, content for the note.
            name: str/list, name for the note. Supports list, it will
            be automatically converted to LastPass path
        """
        if isinstance(name, list):
            name = self.convert_lastpass_path(name)

        print_content = ["printf", note]
        add_note_command = [self.LPASS_MAIN_COMMAND,
                            "add",
                            f"--note-type={note_type}",
                            name,
                            "--non-interactive",
                            "--sync=now"]

        _, code = self._run_piped(print_content, add_note_command)

        return code

    def is_logged_in(self):
        """
        lpass status

        returns: bool, whether the user is logged in and it matches the username
        provided.
        """
        status_command = [self.LPASS_MAIN_COMMAND,
                          "status"]
        process = self._run_command(status_command)
        process.wait()
        match = re.match(self.LPASS_STATUS_REGEX, process.stdout.read().decode())

        return match is not None and match["user"] == self.username

    def ls(self, group=""):
        """
        lpass ls --sync=now [GROUP]

        params:
            group: str/list (optional). Group to filter entries. Supports string (delimit
            each group by \\)

        returns: list, list of filtered entries
        """
        if isinstance(group, list):
            group = self.convert_lastpass_path(group)

        ls_command = [self.LPASS_MAIN_COMMAND, "ls", "--sync=now"]

        output = self._run_command(ls_command, stdout=self._stdout)

        parsed = map(lambda entry: entry.decode(), output.stdout.read().splitlines())
        filtered = list(filter(lambda entry: entry.startswith(group), parsed))
        return filtered

    def show(self, id_=None, path=None, field=None, json_format=False):
        """
        lpass show --sync=now [--json] --id UNIQUEID --field=FIELD [UNIQUENAME]

        params:
            id_: str, LastPass object id. Will make path param have no effect
            path: str, path for object. Subfolders must be delimited by \\ (two backslashes)
            field: str, field to retrieve from object.
            json_format: bool, wether to return the object as a dictionary (will make
            parameter field have no effect)
        """
        show_command = [self.LPASS_MAIN_COMMAND, "show", "--sync=now"]

        if id_:
            show_command.append("--id")
            show_command.append(id_)
        elif path:
            if isinstance(path, list):
                path = self.convert_lastpass_path(path)
            show_command.append(path)
        else:
            raise ValueError("ID or object path must be stated to retrieve an object from vault")

        if field:
            show_command.append(f"--field={field}")

        if json_format:
            show_command.append("--json")

        proc = self._run_command(show_command)

        if proc.wait() != 0:
            vars_to_show = locals().copy()
            _ = vars_to_show.pop("self", None) and vars_to_show.pop("proc", None) and vars_to_show.pop("show_command")
            vars_to_show = json.dumps(vars_to_show, indent=2)

            raise FileNotFoundError(f"No object stored in LastPass account {self.username} with the following attributes:\n{vars_to_show}")

        output = proc.stdout

        if json_format:
            return json.load(output)[0]

        return output.read().decode()

    def get_object_from_path(self, path):
        """
        Get a LastPass object from its path.

        params:
            path: str/list, object's path

        returns: dict, LastPass object.
        """
        if isinstance(path, list):
            path = self.convert_lastpass_path(path)

        id_ = re.search(self.LPASS_ID_REGEX, path)

        if id_ and id_['id'] != '0':
            return self.show(id_=id_['id'], json_format=True)

        path_ = re.sub(self.LPASS_ID_REGEX, "", path)
        return self.show(path=path_, json_format=True)

    @staticmethod
    def convert_lastpass_path(path: list):
        """
        Convert a list into LastPass-formatted path.
        If last element is an empty string, the previous one will be interpreted
        as a folder.

        params:
            path: list, list of folders and/or file.

        returns: str, a LastPass-formatted path
        """
        if not isinstance(path, list):
            raise TypeError("Path must be list")

        fullpath = ""
        for i, element in enumerate(path):
            try:
                if str(path[i + 1]) == "" and i == len(path) - 2:
                    fullpath += element
                    break
            except IndexError:
                pass

            if (i == 0 and element.startswith("Shared-")) or i == len(path) - 2:
                fullpath += element + "/"

            elif i < len(path) - 2:
                fullpath += element + "\\"

            else:
                fullpath += element

        return fullpath

    def logout(self):
        """
        lpass logout --force
        """
        logout_command = [self.LPASS_MAIN_COMMAND, "logout", "--force"]

        self._run_command(logout_command)
