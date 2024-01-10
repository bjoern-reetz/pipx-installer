# install-pipx

A script to easily install pipx into its own virtual environment in just one line.

The defaults respect the [XDG Base Directory Specification](https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html). The script also ensures pipx and the packages that will be installed with it are available on the $PATH.

```bash
curl -sSL https://raw.githubusercontent.com/bjoern-reetz/pipx-installer/main/src/install_pipx.py | python3 -
```

Full usage:

```
usage: install-pipx [-h] [-i INSTALL_DIR] [--no-ensurepath] [-f] [--dry-run] [--log-config LOG_CONFIG | -v | -q]

A script to easily install pipx into its own virtual environment in just one line.

options:
  -h, --help            show this help message and exit
  -i INSTALL_DIR, --install-dir INSTALL_DIR
                        The venv for pipx will be created here. (Default: $XDG_DATA_HOME/pipx-venv or ~/.local/share/pipx-venv if unset)
  --no-ensurepath       After installation, calling pipx ensurepath and creating a symlink will both be skipped.
  -f, --force           Overwrite existing files without warning.
  --dry-run             Perform a dry run, i.e. do not write anything to disk.
  --log-config LOG_CONFIG
                        Path to a JSON or INI file containing advanced logging configuration.
  -v, --verbose         Increase logging level.
  -q, --quiet           Decrease logging level.
```
