from __future__ import annotations

import argparse
import json
import logging
import logging.config
import os
import os.path
import subprocess
import venv
from pathlib import Path

logger = logging.getLogger("pipx-installer")

DEFAULT_USE_SYMLINKS = os.name != "nt"
XDG_DATA_HOME = Path(os.getenv("XDG_DATA_HOME", "~/.local/share")).expanduser()
DEFAULT_ENV_DIR = XDG_DATA_HOME / "pipx-venv"

SYMLINKS_HELP = "Try to use symlinks rather than copies."
COPIES_HELP = "Try to use copies rather than symlinks."
if DEFAULT_USE_SYMLINKS:
    SYMLINKS_HELP += " On the current platform, this is the default."
    COPIES_HELP += " On the current platform, the default is to use symlinks."
else:
    SYMLINKS_HELP += " On the current platform, the default is to use copies."
    COPIES_HELP += " On the current platform, this is the default."
ENV_DIR_HELP = (
    "A directory to create the environment in. "
    f"In the current context, {DEFAULT_ENV_DIR} is the default."
)

DEFAULT_PIPX_BIN_DIR = Path.home() / ".local/bin"
LOCAL_BIN_DIR = Path(os.environ.get("PIPX_BIN_DIR", DEFAULT_PIPX_BIN_DIR)).resolve()
CORE_VENV_DEPS = ("pip", "setuptools")

parser = argparse.ArgumentParser(
    prog="install-pipx",
    description="Creates virtual Python environments and installs pipx into it. "
    "The default location is chosen according to the XDG Base Directory Specification.",
    epilog="After installing pipx with this script,"
    " the pipx command should be available from anywhere without activating any environment.",
)
parser.add_argument(
    "env_dir",
    nargs="?",
    default=DEFAULT_ENV_DIR,
    metavar="ENV_DIR",
    help=ENV_DIR_HELP,
)

arg_group_venv = parser.add_argument_group("Options for environment creation")
arg_group_venv.add_argument(
    "--system-site-packages",
    default=False,
    action="store_true",
    help="Give the virtual environment access to the system site-packages dir.",
)
mutex_group_symlinks = arg_group_venv.add_mutually_exclusive_group()
mutex_group_symlinks.add_argument(
    "--symlinks",
    default=DEFAULT_USE_SYMLINKS,
    action="store_true",
    dest="symlinks",
    help=SYMLINKS_HELP,
)
mutex_group_symlinks.add_argument(
    "--copies",
    default=not DEFAULT_USE_SYMLINKS,
    action="store_false",
    dest="symlinks",
    help=COPIES_HELP,
)
arg_group_venv.add_argument(
    "--clear",
    default=False,
    action="store_true",
    dest="clear",
    help="Delete the contents of the environment directory if it already exists, before environment creation.",
)
arg_group_venv.add_argument(
    "--prompt", help="Provides an alternative prompt prefix for this environment."
)
arg_group_venv.add_argument(
    "--upgrade-deps",
    default=False,
    action="store_true",
    dest="upgrade_deps",
    help="Before installing pipx, upgrade core dependencies "
    f"(i.e. {', '.join(CORE_VENV_DEPS)}) to their latest versions.",
)

arg_group_pipx = parser.add_argument_group("Options related to pipx")
arg_group_pipx.add_argument(
    "--no-ensure-path",
    action="store_false",
    dest="ensure_path",
    help="Skip both calling pipx ensurepath and creating a symlink after installation. "
    "When using this option, the pipx command will not be globally available.",
)

parser.add_argument(
    "--dry-run",
    action="store_true",
    help="Perform a dry run, i.e. do not write anything to disk.",
)
mutex_group_logging = parser.add_mutually_exclusive_group()
mutex_group_logging.add_argument(
    "--log-config",
    help="Path to a JSON or INI file containing advanced logging configuration.",
)
mutex_group_logging.add_argument(
    "-v", "--verbose", action="count", default=0, help="Increase logging level."
)
mutex_group_logging.add_argument(
    "-q", "--quiet", action="count", default=0, help="Decrease logging level."
)


def cli(
    *,
    env_dir: str,
    system_site_packages: bool,
    clear: bool,
    symlinks: bool,
    prompt: str | None,
    upgrade_deps: bool,
    ensure_path: bool,
    dry_run: bool,
    log_config: str | None,
    verbose: int,
    quiet: int,
):
    level = logging.INFO + 10 * (quiet - verbose)
    setup_logging(
        log_config=log_config,
        level=level,
    )

    normalized_env_dir = Path(env_dir).expanduser().resolve()

    logger.info("creating Python environment in %s", normalized_env_dir)
    if not dry_run:
        # EnvBuilder.create creates the environment directory
        # and all necessary subdirectories that don't already exist
        venv.EnvBuilder(
            system_site_packages=system_site_packages,
            clear=clear,
            symlinks=symlinks,
            with_pip=True,
            prompt=prompt,
        ).create(normalized_env_dir)

    pip = os.fspath(normalized_env_dir / "bin/pip")

    # Starting with Python 3.9, EnvBuilder has an upgrade_deps parameter.
    # But because we want to support Python 3.8 as well, we need to implement it ourselves.
    if upgrade_deps:
        logger.info("upgrading core dependencies: %s", ", ".join(CORE_VENV_DEPS))
        if not dry_run:
            subprocess.run([pip, "install", "--upgrade", *CORE_VENV_DEPS], check=True)  # noqa: S603

    logger.info("installing pipx")
    if not dry_run:
        subprocess.run([pip, "install", "pipx"], check=True)  # noqa: S603

    pipx = os.fspath(normalized_env_dir / "bin/pipx")

    if ensure_path:
        pipx_symlink = LOCAL_BIN_DIR / "pipx"

        logger.info("calling pipx ensurepath")
        if not dry_run:
            subprocess.run([pipx, "ensurepath"], check=True)  # noqa: S603

        logger.info("creating symlink to pipx in %s", LOCAL_BIN_DIR)
        if not dry_run:
            pipx_symlink.symlink_to(pipx)


def setup_logging(
    *, log_config: str | os.PathLike | None = None, level: int = logging.INFO
):
    if log_config:
        log_config_path = Path(log_config).expanduser().resolve()
        if log_config_path.suffix == ".json":
            logging.config.dictConfig(json.loads(log_config_path.read_text()))
            logger.debug(
                'Log config was loaded from "%s" via dictConfig.', log_config_path
            )
        else:
            logging.config.fileConfig(str(log_config_path))
            logger.debug(
                'Log config was loaded from "%s" via fileConfig.', log_config_path
            )
        return

    logging.basicConfig(level=level)
    logger.debug("Logging level was set to %s.", logging.getLevelName(level))


def main():
    cli(**vars(parser.parse_args()))


if __name__ == "__main__":
    main()
