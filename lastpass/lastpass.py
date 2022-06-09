import os
import subprocess
from .exceptions import WrongCredentialsException

class Vault():

    LPASS_MAIN_COMMAND = "lpass"
    LPASS_DISABLE_PINENTRY = "LPASS_DISABLE_PINENTRY"
    PINENTRY_DISABLED = "1"

    def __init__(self, username, password, otp=None):
        self._username = username
        self._setup()
        self._authenticate(password, otp)

    ###
    ## Private methods
    ###
    
    def _setup(self):
        self._env = os.environ.copy()
        self._env[self.LPASS_DISABLE_PINENTRY] = self.PINENTRY_DISABLED
        self._stdout = subprocess.PIPE
    
    def _authenticate(self, password, otp=None):
        secrets = password
        if otp:
            secrets += fr"\n{otp}"
        
        secrets_command = ["printf", secrets]
        login_command = [self.LPASS_MAIN_COMMAND, "login", self.username, "--trust"]

        code = self._run_piped(secrets_command, login_command, stdout=subprocess.DEVNULL)

        if code != 0:
            raise WrongCredentialsException(f"Invalid username, password or OTP code.")

    def _run_piped(self, piped_command, main_command, stdout=None):
        piped_proc = self._run_command(piped_command)
        main_proc = self._run_command(main_command, stdout=stdout, stdin=piped_proc.stdout)

        main_proc.communicate()

        return main_proc.wait()

    def _run_command(self, args_list, stdout=None, stdin=None):
        if stdout is None:
            stdout = self._stdout
        return subprocess.Popen(args_list, env=self._env, stdout=stdout, stdin=stdin)
    
    ###
    ## Properties
    ###

    @property
    def username(self):
        return self._username

    ###
    ## Public methods
    ###
    
    def add_note(self, note_type, note, name):
        print_content = ["printf", note]
        add_note_command = [self.LPASS_MAIN_COMMAND,
                            "add",
                            f"--note-type={note_type}",
                            name,
                            "--non-interactive",
                            "--sync=now"]

        self._run_piped(print_content, add_note_command)
