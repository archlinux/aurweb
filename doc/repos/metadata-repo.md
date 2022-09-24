# Repository: metadata-repo

## Overview

The resulting repository contains RPC `type=info` JSON data for packages,
split into two different files:

- `pkgbase.json` contains details about each package base in the AUR
- `pkgname.json` contains details about each package in the AUR

See [Data](#data) for a breakdown of how data is presented in this
repository based off of a RPC `type=info` base.

See [File Layout](#file-layout) for a detailed summary of the layout
of these files and the data contained within.

**NOTE: `Popularity` now requires a client-side calculation, see [Popularity Calculation](#popularity-calculation).**

## Data

This repository contains RPC `type=info` data for all packages found
in AUR's database, reorganized to be suitable for Git repository
changes.

- `pkgname.json` holds Package-specific metadata
    - Some fields have been removed from `pkgname.json` objects
        - `ID`
        - `PackageBaseID -> ID` (moved to `pkgbase.json`)
        - `NumVotes` (moved to `pkgbase.json`)
        - `Popularity` (moved to `pkgbase.json`)
- `pkgbase.json` holds PackageBase-specific metadata
    - Package Base fields from `pkgname.json` have been moved over to
      `pkgbase.json`
        - `ID`
        - `Keywords`
        - `FirstSubmitted`
        - `LastModified`
        - `OutOfDate`
        - `Maintainer`
        - `URLPath`
        - `NumVotes`
        - `Popularity`
        - `PopularityUpdated`

## Popularity Calculation

Clients intending to use popularity data from this archive **must**
perform a decay calculation on their end to reflect a close approximation
of up-to-date popularity.

Putting this step onto the client allows the server to maintain
less popularity record updates, dramatically improving archiving
of popularity data. The same calculation is done on the server-side
when producing outputs for RPC `type=info` and package pages.

```
Let T = Current UTC timestamp in seconds
Let PU = PopularityUpdated timestamp in seconds

# The delta between now and PU in days
Let D = (T - PU) / 86400

# Calculate up-to-date popularity:
P = Popularity * (0.98^D)
```

We can see that the resulting up-to-date popularity value decays as
the exponent is increased:
- `1.0 * (0.98^1) = 0.98`
- `1.0 * (0.98^2) = 0.96039999`
- ...

This decay calculation is essentially pushing back the date found for
votes by the exponent, which takes into account the time-factor. However,
since this calculation is based off of decimals and exponents, it
eventually becomes imprecise. The AUR updates these records on a forced
interval and whenever a vote is added to or removed from a particular package
to avoid imprecision from being an issue for clients

## File Layout

#### pkgbase.json:

    {
        "pkgbase1": {
            "FirstSubmitted": 123456,
            "ID": 1,
            "LastModified": 123456,
            "Maintainer": "kevr",
            "OutOfDate": null,
            "URLPath": "/cgit/aur.git/snapshot/pkgbase1.tar.gz",
            "NumVotes": 1,
            "Popularity": 1.0,
            "PopularityUpdated": 12345567753.0
        },
        ...
    }

#### pkgname.json:

    {
        "pkg1": {
            "CheckDepends": [], # Only included if a check dependency exists
            "Conflicts": [],    # Only included if a conflict exists
            "Depends": [],      # Only included if a dependency exists
            "Description": "some description",
            "Groups": [],       # Only included if a group exists
            "ID": 1,
            "Keywords": [],
            "License": [],
            "MakeDepends": [],  # Only included if a make dependency exists
            "Name": "pkg1",
            "OptDepends": [],   # Only included if an opt dependency exists
            "PackageBase": "pkgbase1",
            "Provides": [],     # Only included if `provides` is defined
            "Replaces": [],     # Only included if `replaces` is defined
            "URL": "https://some_url.com",
            "Version": "1.0-1"
        },
        ...
    }
