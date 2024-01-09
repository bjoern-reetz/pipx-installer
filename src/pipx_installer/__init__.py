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
PREFERRED_BIN_DIRS = ["~/.local/bin", "~/bin"]


def _get_default_bin_dir():
    env_path = os.getenv("PATH")
    env_home = os.getenv("HOME")
    paths = env_path.split(":")
    for bin_dir in PREFERRED_BIN_DIRS:
        if os.path.expanduser(bin_dir) in paths:  # noqa: PTH111
            return bin_dir
    for bin_dir in reversed(paths):
        if bin_dir.startswith(env_home):
            return bin_dir
    for bin_dir in reversed(paths):
        test_file = pathlib.Path(bin_dir) / "pipx"
        try:
            test_file.touch(exist_ok=False)
        except OSError:
            continue
        else:
            test_file.unlink()
            return bin_dir


DEFAULT_BIN_DIR = _get_default_bin_dir()
BIN_DIR_HELP = "Use BIN_DIR for the symlink to the pipx executable."
if DEFAULT_BIN_DIR is None:
    BIN_DIR_HELP += " (Required.)"
else:
    BIN_DIR_HELP += f" (Default: {DEFAULT_BIN_DIR})"


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

parser_group_bin_dir = parser.add_mutually_exclusive_group()
parser_group_bin_dir.add_argument(
    "-b",
    "--bin-dir",
    default=DEFAULT_BIN_DIR,
    help=BIN_DIR_HELP,
)
parser_group_bin_dir.add_argument(
    "--no-export-bin",
    action="store_true",
    help="Skip creating a symlink to the pipx executable.",
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
    bin_dir: str,
    no_export_bin: bool,
    log_config: str,
    verbose: int,
    quiet: int,
):
    setup_logging(
        log_config=log_config,
        verbose=verbose,
        quiet=quiet,
    )

    if not bin_dir and not no_export_bin:
        logger.critical(
            "Could not determine a suitable BIN_DIR. Please either specify --bin-dir or --no-export-bin."
        )

    create_venv(install_dir, force=force, dry_run=dry_run)
    install_pipx(install_dir, dry_run=dry_run)

    if no_export_bin:
        logger.debug("Skip creating a symlink of pipx executable.")
        return

    export_bin(
        install_dir=install_dir,
        bin_dir=bin_dir,
        dry_run=dry_run,
    )


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
        subprocess.run(
            [pip, "install", "pipx"],  # noqa: S603
            check=True,
        )


def export_bin(
    *,
    install_dir: str | os.PathLike,
    bin_dir: str | os.PathLike,
    dry_run=False,
):
    install_dir_path = pathlib.Path(install_dir).expanduser().resolve()
    bin_dir_path = pathlib.Path(bin_dir).expanduser().resolve()

    pipx_bin_path = install_dir_path / "bin/pipx"
    pipx_symlink_path = bin_dir_path / "pipx"
    logger.info('Creating symlink at "%s".', pipx_symlink_path)
    if not dry_run:
        pipx_symlink_path.symlink_to(pipx_bin_path)


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
