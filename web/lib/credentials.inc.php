<?php

define("CRED_ACCOUNT_CHANGE_TYPE", 1);
define("CRED_ACCOUNT_EDIT", 2);
define("CRED_ACCOUNT_EDIT_DEV", 3);
define("CRED_ACCOUNT_LAST_LOGIN", 4);
define("CRED_ACCOUNT_SEARCH", 5);
define("CRED_COMMENT_DELETE", 6);
define("CRED_COMMENT_VIEW_DELETED", 22);
define("CRED_COMMENT_EDIT", 25);
define("CRED_COMMENT_PIN", 26);
define("CRED_PKGBASE_ADOPT", 7);
define("CRED_PKGBASE_SET_KEYWORDS", 8);
define("CRED_PKGBASE_DELETE", 9);
define("CRED_PKGBASE_DISOWN", 10);
define("CRED_PKGBASE_EDIT_COMAINTAINERS", 24);
define("CRED_PKGBASE_FLAG", 11);
define("CRED_PKGBASE_LIST_VOTERS", 12);
define("CRED_PKGBASE_NOTIFY", 13);
define("CRED_PKGBASE_UNFLAG", 15);
define("CRED_PKGBASE_VOTE", 16);
define("CRED_PKGREQ_FILE", 23);
define("CRED_PKGREQ_CLOSE", 17);
define("CRED_PKGREQ_LIST", 18);
define("CRED_TU_ADD_VOTE", 19);
define("CRED_TU_LIST_VOTES", 20);
define("CRED_TU_VOTE", 21);

/**
 * Determine if a user has the permission to perform a given action
 *
 * @param int $credential The type of action to peform
 * @param array $approved_users A user whitelist for this query
 *
 * @return bool Return true if the user has the permission, false if not
 */
function has_credential($credential, $approved_users=array()) {
	if (!isset($_COOKIE['AURSID'])) {
		return false;
	}

	$uid = uid_from_sid($_COOKIE['AURSID']);
	if (in_array($uid, $approved_users)) {
		return true;
	}

	$atype = account_from_sid($_COOKIE['AURSID']);

	switch ($credential) {
	case CRED_PKGBASE_FLAG:
	case CRED_PKGBASE_NOTIFY:
	case CRED_PKGBASE_VOTE:
	case CRED_PKGREQ_FILE:
		return ($atype == 'User' || $atype == 'Trusted User' ||
			$atype == 'Developer' ||
			$atype == 'Trusted User & Developer');
	case CRED_ACCOUNT_CHANGE_TYPE:
	case CRED_ACCOUNT_EDIT:
	case CRED_ACCOUNT_LAST_LOGIN:
	case CRED_ACCOUNT_SEARCH:
	case CRED_COMMENT_DELETE:
	case CRED_COMMENT_VIEW_DELETED:
	case CRED_COMMENT_EDIT:
	case CRED_COMMENT_PIN:
	case CRED_PKGBASE_ADOPT:
	case CRED_PKGBASE_SET_KEYWORDS:
	case CRED_PKGBASE_DELETE:
	case CRED_PKGBASE_EDIT_COMAINTAINERS:
	case CRED_PKGBASE_DISOWN:
	case CRED_PKGBASE_LIST_VOTERS:
	case CRED_PKGBASE_UNFLAG:
	case CRED_PKGREQ_CLOSE:
	case CRED_PKGREQ_LIST:
		return ($atype == 'Trusted User' || $atype == 'Developer' ||
			$atype == 'Trusted User & Developer');
	case CRED_TU_ADD_VOTE:
	case CRED_TU_LIST_VOTES:
	case CRED_TU_VOTE:
		return ($atype == 'Trusted User' ||
			$atype == 'Trusted User & Developer');
	case CRED_ACCOUNT_EDIT_DEV:
		return ($atype == 'Developer' ||
			$atype == 'Trusted User & Developer');
	}

	return false;
}
