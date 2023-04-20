import argparse
import os


# Use a custom parser that lets us require a variable from one of CLI or environment variable,
# this way we can pass creds through CLI for local testing but via environment variables in CI
class EnvDefault(argparse.Action):
    """Argument parser that accepts input from CLI (preferred) or an environment variable

    If a value is not specified in the CLI argument, the content of the environment variable
    named `envvar` is used.  If this environment variable is also empty, the parser will fail
    citing a missing required argument

    Note this Action does not accept the `required` and `default` kwargs and will set them itself
    as appropriate.

    Modified from https://stackoverflow.com/a/10551190/5394584
    """
    def __init__(self, option_strings, dest, envvar, **kwargs):
        # Determine the values for `required` and `default` based on whether defaults are available
        # from an environment variable
        required = False
        if not kwargs["default"]:
            if envvar:
                if envvar in os.environ:
                    # An environment variable of this name exists, use that as a default
                    kwargs["default"] = os.environ[envvar]
                else:
                    # We have no default, require a value from the CLI
                    required = True
                    kwargs["default"] = None
            else:
                raise ValueError(f"EnvDefault requires non-null envvar, got '{envvar}'")
        self.envvar = envvar

        super(EnvDefault, self).__init__(option_strings, dest, required=required, **kwargs)

    def __call__(self, parser, namespace, values, option_string):
        # Actually set values to the destination arg in the namespace
        setattr(namespace, self.dest, values)


def pytest_addoption(parser):
    parser.addoption("--proxy", action="store", help="Proxy to use")
    parser.addoption("--url", action="store", help="Kubeflow dashboard URL")
    parser.addoption("--headful", action="store_true", help="Juju model")

    username_envvar = "KUBEFLOW_AUTH_USERNAME"
    parser.addoption(
        "--username",
        action=EnvDefault,
        envvar=username_envvar,
        default="admin",
        help=f"Dex username (email address).  Required, but can be passed either through CLI or "
             f"via environment variable '{username_envvar}",
    )

    password_envvar = "KUBEFLOW_AUTH_PASSWORD"
    parser.addoption(
        "--password",
        action=EnvDefault,
        envvar=password_envvar,
        default="admin",
        help=f"Dex password.  Required, but can be passed either through CLI or "
             f"via environment variable '{password_envvar}"
    )
