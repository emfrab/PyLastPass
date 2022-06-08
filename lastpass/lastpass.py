import os
import subprocess
from .exceptions import WrongCredentialsException

class LastPass():

    LPASS_MAIN_COMMAND = "lpass"
    LPASS_DISABLE_PINENTRY = "LPASS_DISABLE_PINENTRY"
    PINENTRY_DISABLED = "1"

    def __init__(self, username, password, otp=None):
        self._username = username
        self._setup()
        self._authenticate(password, otp)
    
    def _setup(self):
        self._env = os.environ.copy()
        self._env[self.LPASS_DISABLE_PINENTRY] = self.PINENTRY_DISABLED
        self._stdout = subprocess.PIPE
    
    def _authenticate(self, password, otp=None):
        secrets = password
        if otp:
            secrets += fr"\n{otp}"
        
        secrets_command = ["printf", secrets]
        secrets_proc = self._run_command(secrets_command)

        login_command = [self.LPASS_MAIN_COMMAND, "login", self.username, "--trust"]

        proc = self._run_command(login_command, stdin=secrets_proc.stdout)
        proc.communicate()
        code = proc.wait()

        if code != 0:
            raise WrongCredentialsException(f"Invalid username, password or OTP code.")

    def _run_command(self, args_list, stdout=None, stdin=None):
        if stdout is None:
            stdout = self._stdout
        return subprocess.Popen(args_list, env=self._env, stdout=stdout, stdin=stdin)
    
    @property
    def username(self):
        return self._username

