import re
from setuptools import setup, find_packages
import sys

version = None
with open('web/lib/version.inc.php', 'r') as f:
    for line in f.readlines():
        match = re.match(r'^define\("AURWEB_VERSION", "v([0-9.]+)"\);$', line)
        if match:
            version = match.group(1)

if not version:
    sys.stderr.write('error: Failed to parse version file!')
    sys.exit(1)

setup(
    name="aurweb",
    version=version,
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'aurweb-git-auth = aurweb.git.auth:main',
            'aurweb-git-serve = aurweb.git.serve:main',
            'aurweb-git-update = aurweb.git.update:main',
            'aurweb-aurblup = aurweb.scripts.aurblup:main',
            'aurweb-mkpkglists = aurweb.scripts.mkpkglists:main',
            'aurweb-notify = aurweb.scripts.notify:main',
            'aurweb-pkgmaint = aurweb.scripts.pkgmaint:main',
            'aurweb-popupdate = aurweb.scripts.popupdate:main',
            'aurweb-tuvotereminder = aurweb.scripts.tuvotereminder:main',
        ],
    },
)
