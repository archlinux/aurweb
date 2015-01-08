#!/usr/bin/python3

import configparser
import os
import shutil
import sys

config = configparser.RawConfigParser()
config.read(os.path.dirname(os.path.realpath(__file__)) + "/../../conf/config")

template_path = config.get('serve', 'template-path')
git_update_hook = config.get('serve', 'git-update-hook')

def die(msg):
    sys.stderr.write("%s\n" % (msg))
    exit(1)

if os.path.exists(template_path):
    shutil.rmtree(template_path)

os.mkdir(template_path)
os.chdir(template_path)
os.mkdir("branches")
os.mkdir("hooks")
os.mkdir("info")
os.symlink(git_update_hook, template_path + 'hooks/update')

with open("description", 'w') as f:
    f.write("Unnamed repository; push to update the description.\n")
