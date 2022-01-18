"""
Add a user to the configured aurweb database.

See `aurweb-adduser --help` for documentation.

Copyright (C) 2022 aurweb Development Team
All Rights Reserved
"""
import argparse
import sys
import traceback

import aurweb.models.account_type as at

from aurweb import db
from aurweb.models.account_type import AccountType
from aurweb.models.ssh_pub_key import SSHPubKey, get_fingerprint
from aurweb.models.user import User


def parse_args():
    parser = argparse.ArgumentParser(description="aurweb-adduser options")

    parser.add_argument("-u", "--username", help="Username", required=True)
    parser.add_argument("-e", "--email", help="Email", required=True)
    parser.add_argument("-p", "--password", help="Password", required=True)
    parser.add_argument("-r", "--realname", help="Real Name")
    parser.add_argument("-i", "--ircnick", help="IRC Nick")
    parser.add_argument("--pgp-key", help="PGP Key Fingerprint")
    parser.add_argument("--ssh-pubkey", help="SSH PubKey")

    choices = at.ACCOUNT_TYPE_NAME.values()
    parser.add_argument("-t", "--type", help="Account Type",
                        choices=choices, default=at.USER)

    return parser.parse_args()


def main():
    args = parse_args()

    db.get_engine()
    type = db.query(AccountType,
                    AccountType.AccountType == args.type).first()
    with db.begin():
        user = db.create(User, Username=args.username,
                         Email=args.email, Passwd=args.password,
                         RealName=args.realname, IRCNick=args.ircnick,
                         PGPKey=args.pgp_key, AccountType=type)

    if args.ssh_pubkey:
        pubkey = args.ssh_pubkey.strip()

        # Remove host from the pubkey if it's there.
        pubkey = ' '.join(pubkey.split(' ')[:2])

        with db.begin():
            db.create(SSHPubKey,
                      User=user,
                      PubKey=pubkey,
                      Fingerprint=get_fingerprint(pubkey))

    print(user.json())
    return 0


if __name__ == "__main__":
    e = 1
    try:
        e = main()
    except Exception:
        traceback.print_exc()
        e = 1
    sys.exit(e)
