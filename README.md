# pylastpass

Simple API for [LastPass](https://www.lastpass.com/) password manager. Only compatible with Linux/UNIX environments.

## Prerequisites

- Install [lastpass-cli](https://github.com/lastpass/lastpass-cli) to provide `lpass` command:

    On WSL2:
    ```
    sudo apt-get install lastpass-cli
    ```

## Usage

Copy package manually and import.

Basic usage:

```py
>>> from lastpass import Vault
>>> from getpass import getpass
>>> vault = Vault("example@email.com")
>>> password = getpass("Type vault password: ")
Type vault password:
>>> vault.login(password)                                                                                                                                                                                                                                                                                                        
>>> for item in vault.ls():
...     print(item)
...
MyFolder/Password [id: 291119914326505545776]
>>> print(vault.show(path=r'MyFolder\\Password'))
site.com [id: 291119914326505545776]
Username: example@email.com
Password: password
URL: http://site.com
```
