# Contributing

Patches should be sent to the [aur-dev@lists.archlinux.org][1] mailing list
or included in a merge request on the [aurweb repository][2].

Before sending patches, you are recommended to run `flake8` and `isort`.

You can add a git hook to do this by installing `python-pre-commit` and running
`pre-commit install`.

[1]: https://lists.archlinux.org/listinfo/aur-dev
[2]: https://gitlab.archlinunx.org/archlinux/aurweb

### Coding Guidelines

DISCLAIMER: We realise the code doesn't necessarily follow all the rules.
This is an attempt to establish a standard coding style for future
development.

1. All source modified or added within a patchset **must** maintain equivalent
   or increased coverage by providing tests that use the functionality
2. Please keep your source within an 80 column width
3. Use four space indentation
4. Use [conventional commits](https://www.conventionalcommits.org/en/v1.0.0/)
5. DRY: Don't Repeat Yourself
6. All code should be tested for good _and_ bad cases

Test patches that increase coverage in the codebase are always welcome.
