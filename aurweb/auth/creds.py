from aurweb.models.account_type import (
    DEVELOPER_ID,
    TRUSTED_USER_AND_DEV_ID,
    TRUSTED_USER_ID,
    USER_ID,
)
from aurweb.models.user import User

ACCOUNT_CHANGE_TYPE = 1
ACCOUNT_EDIT = 2
ACCOUNT_EDIT_DEV = 3
ACCOUNT_LAST_LOGIN = 4
ACCOUNT_SEARCH = 5
ACCOUNT_LIST_COMMENTS = 28
COMMENT_DELETE = 6
COMMENT_UNDELETE = 27
COMMENT_VIEW_DELETED = 22
COMMENT_EDIT = 25
COMMENT_PIN = 26
PKGBASE_ADOPT = 7
PKGBASE_SET_KEYWORDS = 8
PKGBASE_DELETE = 9
PKGBASE_DISOWN = 10
PKGBASE_EDIT_COMAINTAINERS = 24
PKGBASE_FLAG = 11
PKGBASE_LIST_VOTERS = 12
PKGBASE_NOTIFY = 13
PKGBASE_UNFLAG = 15
PKGBASE_VOTE = 16
PKGREQ_FILE = 23
PKGREQ_CLOSE = 17
PKGREQ_LIST = 18
TU_ADD_VOTE = 19
TU_LIST_VOTES = 20
TU_VOTE = 21
PKGBASE_MERGE = 29

user_developer_or_trusted_user = set(
    [USER_ID, TRUSTED_USER_ID, DEVELOPER_ID, TRUSTED_USER_AND_DEV_ID]
)
trusted_user_or_dev = set([TRUSTED_USER_ID, DEVELOPER_ID, TRUSTED_USER_AND_DEV_ID])
developer = set([DEVELOPER_ID, TRUSTED_USER_AND_DEV_ID])
trusted_user = set([TRUSTED_USER_ID, TRUSTED_USER_AND_DEV_ID])

cred_filters = {
    PKGBASE_FLAG: user_developer_or_trusted_user,
    PKGBASE_NOTIFY: user_developer_or_trusted_user,
    PKGBASE_VOTE: user_developer_or_trusted_user,
    PKGREQ_FILE: user_developer_or_trusted_user,
    ACCOUNT_CHANGE_TYPE: trusted_user_or_dev,
    ACCOUNT_EDIT: trusted_user_or_dev,
    ACCOUNT_LAST_LOGIN: trusted_user_or_dev,
    ACCOUNT_LIST_COMMENTS: trusted_user_or_dev,
    ACCOUNT_SEARCH: trusted_user_or_dev,
    COMMENT_DELETE: trusted_user_or_dev,
    COMMENT_UNDELETE: trusted_user_or_dev,
    COMMENT_VIEW_DELETED: trusted_user_or_dev,
    COMMENT_EDIT: trusted_user_or_dev,
    COMMENT_PIN: trusted_user_or_dev,
    PKGBASE_ADOPT: trusted_user_or_dev,
    PKGBASE_SET_KEYWORDS: trusted_user_or_dev,
    PKGBASE_DELETE: trusted_user_or_dev,
    PKGBASE_EDIT_COMAINTAINERS: trusted_user_or_dev,
    PKGBASE_DISOWN: trusted_user_or_dev,
    PKGBASE_LIST_VOTERS: trusted_user_or_dev,
    PKGBASE_UNFLAG: trusted_user_or_dev,
    PKGREQ_CLOSE: trusted_user_or_dev,
    PKGREQ_LIST: trusted_user_or_dev,
    TU_ADD_VOTE: trusted_user,
    TU_LIST_VOTES: trusted_user_or_dev,
    TU_VOTE: trusted_user,
    ACCOUNT_EDIT_DEV: developer,
    PKGBASE_MERGE: trusted_user_or_dev,
}


def has_credential(user: User, credential: int, approved: list = tuple()):

    if user in approved:
        return True
    return user.AccountTypeID in cred_filters[credential]
