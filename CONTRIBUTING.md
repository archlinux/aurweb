# Contributing

Patches should be sent to the [aur-dev@archlinux.org][1] mailing list.

Before sending patches, you are recommended to run `flake8` and `isort`.

You can add a git hook to do this by installing `python-pre-commit` and running
`pre-commit install`.

[1] https://lists.archlinux.org/listinfo/aur-dev

### Coding Guidelines

1. All source modified or added within a patchset **must** maintain equivalent
   or increased coverage by providing tests that use the functionality.

2. Please keep your source within an 80 column width.

Test patches that increase coverage in the codebase are always welcome.
