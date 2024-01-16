## v2.0.0 (2024-01-16)

### BREAKING CHANGE

- Some options/arguments have changed name.

### Refactor

- rewrite CLI to support options like python -m venv

## v1.0.0 (2024-01-10)

### BREAKING CHANGE

- The option --bin-dir was removed, the option --no-export-bin was renamed to --no-ensurepath and has a slightly different implementation.

### Fix

- resolve paths consistently
- create symlink to pipx executable

### Refactor

- replace custom implementation by calling pipx ensurepath

## v0.1.1 (2024-01-10)

### Refactor

- refactor package into module
