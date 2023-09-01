from aurweb.models.account_type import (
    DEVELOPER_ID,
    PACKAGE_MAINTAINER_AND_DEV_ID,
    PACKAGE_MAINTAINER_ID,
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
PM_ADD_VOTE = 19
PM_LIST_VOTES = 20
PM_VOTE = 21
PKGBASE_MERGE = 29

user_developer_or_package_maintainer = set(
    [USER_ID, PACKAGE_MAINTAINER_ID, DEVELOPER_ID, PACKAGE_MAINTAINER_AND_DEV_ID]
)
package_maintainer_or_dev = set(
    [PACKAGE_MAINTAINER_ID, DEVELOPER_ID, PACKAGE_MAINTAINER_AND_DEV_ID]
)
developer = set([DEVELOPER_ID, PACKAGE_MAINTAINER_AND_DEV_ID])
package_maintainer = set([PACKAGE_MAINTAINER_ID, PACKAGE_MAINTAINER_AND_DEV_ID])

cred_filters = {
    PKGBASE_FLAG: user_developer_or_package_maintainer,
    PKGBASE_NOTIFY: user_developer_or_package_maintainer,
    PKGBASE_VOTE: user_developer_or_package_maintainer,
    PKGREQ_FILE: user_developer_or_package_maintainer,
    ACCOUNT_CHANGE_TYPE: package_maintainer_or_dev,
    ACCOUNT_EDIT: package_maintainer_or_dev,
    ACCOUNT_LAST_LOGIN: package_maintainer_or_dev,
    ACCOUNT_LIST_COMMENTS: package_maintainer_or_dev,
    ACCOUNT_SEARCH: package_maintainer_or_dev,
    COMMENT_DELETE: package_maintainer_or_dev,
    COMMENT_UNDELETE: package_maintainer_or_dev,
    COMMENT_VIEW_DELETED: package_maintainer_or_dev,
    COMMENT_EDIT: package_maintainer_or_dev,
    COMMENT_PIN: package_maintainer_or_dev,
    PKGBASE_ADOPT: package_maintainer_or_dev,
    PKGBASE_SET_KEYWORDS: package_maintainer_or_dev,
    PKGBASE_DELETE: package_maintainer_or_dev,
    PKGBASE_EDIT_COMAINTAINERS: package_maintainer_or_dev,
    PKGBASE_DISOWN: package_maintainer_or_dev,
    PKGBASE_LIST_VOTERS: package_maintainer_or_dev,
    PKGBASE_UNFLAG: package_maintainer_or_dev,
    PKGREQ_CLOSE: package_maintainer_or_dev,
    PKGREQ_LIST: package_maintainer_or_dev,
    PM_ADD_VOTE: package_maintainer,
    PM_LIST_VOTES: package_maintainer_or_dev,
    PM_VOTE: package_maintainer,
    ACCOUNT_EDIT_DEV: developer,
    PKGBASE_MERGE: package_maintainer_or_dev,
}


def has_credential(user: User, credential: int, approved: list = tuple()):
    if user in approved:
        return True
    return user.AccountTypeID in cred_filters[credential]
