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
)
