from __future__ import annotations

import argparse
import json
import logging
import logging.config
import os
import os.path
import pathlib
import shutil
import subprocess
import venv

logger = logging.getLogger("pipx-installer")

DEFAULT_INSTALL_DIR = os.path.join(  # noqa: PTH118
    os.getenv("XDG_DATA_HOME", "~/.local/share"), "pipx-venv"
)

parser = argparse.ArgumentParser(
    prog="install-pipx",
    description="Install pipx into an isolated Python environment and it globally available.",
)
parser.add_argument(
    "-i",
    "--install-dir",
    default=DEFAULT_INSTALL_DIR,
    help=f"The venv for pipx will be created here. (Default: {DEFAULT_INSTALL_DIR})",
)
parser.add_argument(
    "--no-ensurepath",
    action="store_true",
    help="Do not call pipx ensurepath after installation.",
)

parser.add_argument(
    "-f",
    "--force",
    action="store_true",
    help="Overwrite existing files without warning.",
)
parser.add_argument(
    "--dry-run",
    action="store_true",
    help="Perform a dry run, i.e. do not actually touch anything.",
)

parser_group_logging = parser.add_mutually_exclusive_group()
parser_group_logging.add_argument(
    "--log-config",
    help="Path to a JSON or INI file containing advanced logging configuration.",
)
parser_group_logging.add_argument(
    "-v", "--verbose", action="count", default=0, help="Increase logging level."
)
parser_group_logging.add_argument(
    "-q", "--quiet", action="count", default=0, help="Decrease logging level."
)


def cli(
    *,
    install_dir: str,
    force: bool,
    dry_run: bool,
    no_ensurepath: bool,
    log_config: str,
    verbose: int,
    quiet: int,
):
    setup_logging(
        log_config=log_config,
        verbose=verbose,
        quiet=quiet,
    )

    create_venv(install_dir, force=force, dry_run=dry_run)
    install_pipx(install_dir, dry_run=dry_run)

    if no_ensurepath:
        logger.debug("Skip creating a symlink of pipx executable.")
        return

    call_pipx_ensurepath(install_dir, dry_run=dry_run)


def setup_logging(
    *, log_config: str | os.PathLike | None = None, verbose: int = 0, quiet: int = 0
):
    if log_config:
        log_config_path = pathlib.Path(log_config).expanduser().resolve()
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

    level = logging.INFO + 10 * (quiet - verbose)
    logging.basicConfig(level=level)
    logger.debug("Logging level was set to %s.", logging.getLevelName(level))


def create_venv(install_dir: str | os.PathLike, *, force=False, dry_run=False):
    install_dir_path = pathlib.Path(install_dir).expanduser().resolve()

    if not _is_path_free(install_dir_path, empty_dir_ok=True):
        if not force:
            msg = "The target location already exists."
            raise FileExistsError(msg)

        logger.info("Removing pre-existing target.")
        if not dry_run:
            _remove_path(install_dir_path)

    logger.info("Creating venv at %s", install_dir_path)
    if not dry_run:
        # EnvBuilder.create creates the environment directory
        # and all necessary subdirectories that don't already exist
        venv.EnvBuilder(with_pip=True, symlinks=True).create(install_dir_path)


def install_pipx(install_dir: str | os.PathLike, *, dry_run=False):
    install_dir_path = pathlib.Path(install_dir).expanduser().resolve()

    logger.info('Installing pipx to "%s".', install_dir_path)
    pip = os.fspath(install_dir_path / "bin/pip")
    # todo: pipe output to logger
    # todo: inherit verbosity
    if not dry_run:
        subprocess.run([pip, "install", "pipx"], check=True)  # noqa: S603


def call_pipx_ensurepath(
    install_dir: str | os.PathLike,
    *,
    dry_run=False,
):
    install_dir_path = pathlib.Path(install_dir).expanduser()
    pipx = os.fspath(install_dir_path / "bin/pipx")
    logger.info("Calling pipx ensurepath")
    if not dry_run:
        subprocess.run([pipx, "ensurepath"], check=True)  # noqa: S603


def _is_path_free(target: pathlib.PathLike, *, empty_dir_ok=False):
    target_path = pathlib.Path(target)

    # Path.exists() follows symlinks and hence takes a broken symlink for a non-existent file
    if not target_path.exists() and not target_path.is_symlink():
        return True

    if (
        empty_dir_ok
        and target_path.is_dir()
        and all(False for _ in target_path.iterdir())
    ):
        return True

    return False


def _remove_path(target: pathlib.PathLike):
    target_path = pathlib.Path(target)
    if target_path.is_dir():
        shutil.rmtree(target_path)
    else:
        target_path.unlink()


def main():
    cli(**vars(parser.parse_args()))


if __name__ == "__main__":
    main()
