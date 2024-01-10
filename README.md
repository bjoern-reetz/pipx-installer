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
