# aurweb Git Archive Specification

<span style="color: red">
    WARNING: This aurweb Git Archive implementation is
    experimental and may be changed.
</span>

## Overview

This git archive specification refers to the archive git repositories
created by [aurweb/scripts/git_archive.py](aurweb/scripts/git_archive.py)
using [spec modules](#spec-modules).

## Configuration

- `[git-archive]`
    - `author`
        - Git commit author
    - `author-email`
        - Git commit author email

See an [official spec](#official-specs)'s documentation for spec-specific
configurations.

## Fetch/Update Archives

When a client has not yet fetched any initial archives, they should clone
the repository:

    $ git clone https://aur.archlinux.org/archive.git aurweb-archive

When updating, the repository is already cloned and changes need to be pulled
from remote:

    # To update:
    $ cd aurweb-archive && git pull

For end-user production applications, see
[Minimize Disk Space](#minimize-disk-space).

## Minimize Disk Space

Using `git gc` on the repository will compress revisions and remove
unreachable objects which grow the repository a considerable amount
each commit. It is recommended that the following command is used
after cloning the archive or pulling updates:

    $ cd aurweb-archive && git gc --aggressive

## Spec Modules

Each aurweb spec module belongs to the `aurweb.archives.spec` package. For
example: a spec named "example" would be located at
`aurweb.archives.spec.example`.

[Official spec listings](#official-specs) use the following format:

- `spec_name`
    - Spec description; what this spec produces
        - `<link to repo documentation>`

### Official Specs

- [metadata](doc/specs/metadata.md)
    - Package RPC `type=info` metadata
        - [metadata-repo](repos/metadata-repo.md)
- [users](doc/specs/users.md)
    - List of users found in the database
        - [users-repo](repos/users-repo.md)
- [pkgbases](doc/specs/pkgbases.md)
    - List of package bases found in the database
        - [pkgbases-repo](repos/pkgbases-repo.md)
- [pkgnames](doc/specs/pkgnames.md)
    - List of package names found in the database
        - [pkgnames-repo](repos/pkgnames-repo.md)
