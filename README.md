# install-pipx

A script to easily install pipx into its own virtual environment in just one line.

```bash
curl -sSL https://raw.githubusercontent.com/bjoern-reetz/pipx-installer/main/src/install_pipx.py | python3 -
```

The above command will perform the following steps:

1. create an isolated Python environment
2. install pipx into that environment
3. call pipx ensurepath

It also creates a symlink to the pipx executable in the PIPX_BIN_DIR just like `pipx ensurepath` would do if you had installed it via `pip install --user pipx`.
The default locations are chosen in conformance to the [XDG Base Directory Specification](https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html).
You can preview everything that will be done by appending `--dry-run`.

Full usage:

```
usage: install-pipx [-h] [--system-site-packages] [--symlinks | --copies] [--clear]
                    [--prompt PROMPT] [--upgrade-deps] [--no-ensure-path] [--dry-run]
                    [--log-config LOG_CONFIG | -v | -q]
                    [ENV_DIR]

Creates virtual Python environments and installs pipx into it. The default location is
chosen according to the XDG Base Directory Specification.

positional arguments:
  ENV_DIR               A directory to create the environment in. In the current context,
                        /home/breetz/.local/share/pipx-venv is the default.

options:
  -h, --help            show this help message and exit
  --dry-run             Perform a dry run, i.e. do not write anything to disk.
  --log-config LOG_CONFIG
                        Path to a JSON or INI file containing advanced logging
                        configuration.
  -v, --verbose         Increase logging level.
  -q, --quiet           Decrease logging level.

Options for environment creation:
  --system-site-packages
                        Give the virtual environment access to the system site-packages
                        dir.
  --symlinks            Try to use symlinks rather than copies. On the current platform,
                        this is the default.
  --copies              Try to use copies rather than symlinks. On the current platform,
                        the default is to use symlinks.
  --clear               Delete the contents of the environment directory if it already
                        exists, before environment creation.
  --prompt PROMPT       Provides an alternative prompt prefix for this environment.
  --upgrade-deps        Before installing pipx, upgrade core dependencies (i.e. pip,
                        setuptools) to their latest versions.

Options related to pipx:
  --no-ensure-path      Skip both calling pipx ensurepath and creating a symlink after
                        installation. When using this option, the pipx command will not
                        be globally available.

After installing pipx with this script, the pipx command should be available from
anywhere without activating any environment.
```
