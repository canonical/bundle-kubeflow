import os
import shutil
import subprocess
import sys


def run(*args, env: dict = None, check=True):
    """Runs command and exits script gracefully on errors."""

    print(f'+ {" ".join(args)}')

    if env is None:
        env = os.environ
    else:
        env = {**env, **os.environ}

    result = subprocess.run(args, env=env)

    if check:
        try:
            result.check_returncode()
        except subprocess.CalledProcessError as err:
            if result.stderr:
                print(result.stderr.decode('utf-8'))
            print(err)
            sys.exit(1)


def get_output(*args):
    """Gets output from command"""
    try:
        return subprocess.run(args, check=True, stdout=subprocess.PIPE).stdout.decode('utf-8')
    except subprocess.CalledProcessError as err:
        print(err)
        sys.exit(1)


def require(*commands: str):
    """Checks that required commands are available somewhere on $PATH."""

    # Allow syntax of `command:snap-package` to control the name of the
    # snap package to tell the user to install.
    commands = [c.rsplit(':', 1) for c in commands]

    # Check that the commands exist.
    missing = [c for c in commands if shutil.which(c[0]) is None]

    if missing:
        print('Some dependencies were not found. Please install them with:\n')

        for command in missing:
            print(f'    sudo snap install {command[-1]} --classic')

        print()
        sys.exit(1)
