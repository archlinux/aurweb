#!/usr/bin/env python

from copy import copy, deepcopy
import pprint
import sys

class Attr(object):
    def __init__(self, name, is_multivalued=False, allow_arch_extensions=False):
        self.name = name
        self.is_multivalued = is_multivalued
        self.allow_arch_extensions = allow_arch_extensions

PKGBUILD_ATTRIBUTES = {
    'arch':         Attr('arch',            True),
    'backup':       Attr('backup',          True),
    'changelog':    Attr('changelog',       False),
    'checkdepends': Attr('checkdepends',    True),
    'conflicts':    Attr('conflicts',       True, True),
    'depends':      Attr('depends',         True, True),
    'epoch':        Attr('epoch',           False),
    'groups':       Attr('groups',          True),
    'install':      Attr('install',         False),
    'license':      Attr('license',         True),
    'makedepends':  Attr('makedepends',     True, True),
    'md5sums':      Attr('md5sums',         True, True),
    'noextract':    Attr('noextract',       True),
    'optdepends':   Attr('optdepends',      True, True),
    'options':      Attr('options',         True),
    'pkgname':      Attr('pkgname',         False),
    'pkgrel':       Attr('pkgrel',          False),
    'pkgver':       Attr('pkgver',          False),
    'provides':     Attr('provides',        True, True),
    'replaces':     Attr('replaces',        True, True),
    'sha1sums':     Attr('sha1sums',        True, True),
    'sha224sums':   Attr('sha224sums',      True, True),
    'sha256sums':   Attr('sha256sums',      True, True),
    'sha384sums':   Attr('sha384sums',      True, True),
    'sha512sums':   Attr('sha512sums',      True, True),
    'source':       Attr('source',          True, True),
    'url':          Attr('url',             False),
    'validpgpkeys': Attr('validpgpkeys',    True),
}

def find_attr(attrname):
    # exact match
    attr = PKGBUILD_ATTRIBUTES.get(attrname, None)
    if attr:
        return attr

    # prefix match
    # XXX: this could break in the future if PKGBUILD(5) ever
    # introduces a key which is a subset of another.
    for k in PKGBUILD_ATTRIBUTES.keys():
        if attrname.startswith(k + '_'):
            return PKGBUILD_ATTRIBUTES[k]

def IsMultiValued(attrname):
    attr = find_attr(attrname)
    return attr and attr.is_multivalued

class AurInfo(object):
    def __init__(self):
        self._pkgbase = {}
        self._packages = {}

    def GetPackageNames(self):
        return self._packages.keys()

    def GetMergedPackage(self, pkgname):
        package = deepcopy(self._pkgbase)
        package['pkgname'] = pkgname
        for k, v in self._packages.get(pkgname).items():
            package[k] = deepcopy(v)
        return package

    def AddPackage(self, pkgname):
        self._packages[pkgname] = {}
        return self._packages[pkgname]

    def SetPkgbase(self, pkgbasename):
        self._pkgbase = {'pkgname' : pkgbasename}
        return self._pkgbase


class StderrECatcher(object):
    def Catch(self, lineno, error):
        print('ERROR[{:d}]: {:s}'.format(lineno, error), file=sys.stderr)


class CollectionECatcher(object):
    def __init__(self):
        self._errors = []

    def Catch(self, lineno, error):
        self._errors.append((lineno, error))

    def HasErrors(self):
        return len(self._errors) > 0

    def Errors(self):
        return copy(self._errors)


def ParseAurinfoFromIterable(iterable, ecatcher=None):
    aurinfo = AurInfo()

    if ecatcher is None:
        ecatcher = StderrECatcher()

    current_package = None
    lineno = 0

    for line in iterable:
        lineno += 1

        if line.startswith('#'):
            continue

        if not line.strip():
            # end of package
            current_package = None
            continue

        if not (line.startswith('\t') or line.startswith(' ')):
            # start of new package
            try:
                key, value = map(str.strip, line.split('=', 1))
            except ValueError:
                ecatcher.Catch(lineno, 'unexpected header format in section={:s}'.format(
                               current_package['pkgname']))
                continue

            if key == 'pkgbase':
                current_package = aurinfo.SetPkgbase(value)
            elif key == 'pkgname':
                current_package = aurinfo.AddPackage(value)
            else:
                ecatcher.Catch(lineno, 'unexpected new section not starting '
                               'with \'pkgname\' found')
                continue
        else:
            # package attribute
            if current_package is None:
                ecatcher.Catch(lineno, 'package attribute found outside of '
                               'a package section')
                continue

            try:
                key, value = map(str.strip, line.split('=', 1))
            except ValueError:
                ecatcher.Catch(lineno, 'unexpected attribute format in '
                                       'section={:s}'.format(current_package['pkgname']))

            if IsMultiValued(key):
                if not current_package.get(key):
                    current_package[key] = []
                if value:
                    current_package[key].append(value)
            else:
                if not current_package.get(key):
                    current_package[key] = value
                else:
                    ecatcher.Catch(lineno, 'overwriting attribute '
                                           '{:s}: {:s} -> {:s}'.format(key,
                                           current_package[key], value))

    return aurinfo


def ParseAurinfo(filename='.AURINFO', ecatcher=None):
    with open(filename) as f:
        return ParseAurinfoFromIterable(f, ecatcher)


def ValidateAurinfo(filename='.AURINFO'):
    ecatcher = CollectionECatcher()
    ParseAurinfo(filename, ecatcher)
    errors = ecatcher.Errors()
    for error in errors:
        print('error on line {:d}: {:s}'.format(error), file=sys.stderr)
    return not errors


if __name__ == '__main__':
    pp = pprint.PrettyPrinter(indent=4)

    if len(sys.argv) == 1:
        print('error: not enough arguments')
        sys.exit(1)
    elif len(sys.argv) == 2:
        action = sys.argv[1]
        filename = '.AURINFO'
    else:
        action, filename = sys.argv[1:3]

    if action == 'parse':
        aurinfo = ParseAurinfo()
        for pkgname in aurinfo.GetPackageNames():
            print(">>> merged package: {:s}".format(pkgname))
            pp.pprint(aurinfo.GetMergedPackage(pkgname))
            print()
    elif action == 'validate':
        sys.exit(not ValidateAurinfo(filename))
    else:
        print('unknown action: {:s}'.format(action))
        sys.exit(1)

# vim: set et ts=4 sw=4:
