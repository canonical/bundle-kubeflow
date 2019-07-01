import os
import re
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


def require(*commands):
    """Checks that required commands are available somewhere on $PATH."""

    missing = [c for c in commands if shutil.which(c) is None]

    if missing:
        print('Some dependencies were not found. Please install them with:\n')

        for command in missing:
            # The command might be e.g. `microk8s.enable`, and we want to tell
            # the user to install the main snap name.
            cmd = re.sub(r"\..*", "", command)
            print(f'    sudo snap install {cmd} --classic')

        print()
        sys.exit(1)
