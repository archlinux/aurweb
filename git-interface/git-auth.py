#!/usr/bin/python3

import shlex
import re
import sys

import config
import db


def format_command(env_vars, command, ssh_opts, ssh_key):
    environment = ''
    for key, var in env_vars.items():
        environment += '{}={} '.format(key, shlex.quote(var))

    command = shlex.quote(command)
    command = '{}{}'.format(environment, command)

    # The command is being substituted into an authorized_keys line below,
    # so we need to escape the double quotes.
    command = command.replace('"', '\\"')
    msg = 'command="{}",{} {}'.format(command, ssh_opts, ssh_key)
    return msg


valid_keytypes = config.get('auth', 'valid-keytypes').split()
username_regex = config.get('auth', 'username-regex')
git_serve_cmd = config.get('auth', 'git-serve-cmd')
ssh_opts = config.get('auth', 'ssh-options')

keytype = sys.argv[1]
keytext = sys.argv[2]
if keytype not in valid_keytypes:
    exit(1)

conn = db.Connection()

cur = conn.execute("SELECT Users.Username, Users.AccountTypeID FROM Users " +
                   "INNER JOIN SSHPubKeys ON SSHPubKeys.UserID = Users.ID "
                   "WHERE SSHPubKeys.PubKey = ? AND Users.Suspended = 0",
                   (keytype + " " + keytext,))

if cur.rowcount != 1:
    exit(1)

user, account_type = cur.fetchone()
if not re.match(username_regex, user):
    exit(1)


env_vars = {
    'AUR_USER': user,
    'AUR_PRIVILEGED': '1' if account_type > 1 else '0',
}
key = keytype + ' ' + keytext

print(format_command(env_vars, git_serve_cmd, ssh_opts, key))
