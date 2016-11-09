<?php

/**
 * Determine if an HTTP request variable is set
 *
 * @param string $name The request variable to test for
 *
 * @return string Return the value of the request variable, otherwise blank
 */
function in_request($name) {
	if (isset($_REQUEST[$name])) {
		return $_REQUEST[$name];
	}
	return "";
}

/**
 * Format the PGP key fingerprint
 *
 * @param string $fingerprint An unformatted PGP key fingerprint
 *
 * @return string PGP fingerprint with spaces every 4 characters
 */
function html_format_pgp_fingerprint($fingerprint) {
	if (strlen($fingerprint) != 40 || !ctype_xdigit($fingerprint)) {
		return $fingerprint;
	}

	return htmlspecialchars(substr($fingerprint, 0, 4) . " " .
		substr($fingerprint, 4, 4) . " " .
		substr($fingerprint, 8, 4) . " " .
		substr($fingerprint, 12, 4) . " " .
		substr($fingerprint, 16, 4) . "  " .
		substr($fingerprint, 20, 4) . " " .
		substr($fingerprint, 24, 4) . " " .
		substr($fingerprint, 28, 4) . " " .
		substr($fingerprint, 32, 4) . " " .
		substr($fingerprint, 36, 4) . " ", ENT_QUOTES);
}

/**
 * Loads the account editing form, with any values that are already saved
 *
 * @global array $SUPPORTED_LANGS Languages that are supported by the AUR
 * @param string $A Form to use, either UpdateAccount or NewAccount
 * @param string $U The username to display
 * @param string $T The account type of the displayed user
 * @param string $S Whether the displayed user has a suspended account
 * @param string $E The e-mail address of the displayed user
 * @param string $H Whether the e-mail address of the displayed user is hidden
 * @param string $P The password value of the displayed user
 * @param string $C The confirmed password value of the displayed user
 * @param string $R The real name of the displayed user
 * @param string $L The language preference of the displayed user
 * @param string $HP The homepage of the displayed user
 * @param string $I The IRC nickname of the displayed user
 * @param string $K The PGP key fingerprint of the displayed user
 * @param string $PK The list of SSH public keys
 * @param string $J The inactivity status of the displayed user
 * @param string $CN Whether to notify of new comments
 * @param string $UN Whether to notify of package updates
 * @param string $ON Whether to notify of ownership changes
 * @param string $UID The user ID of the displayed user
 * @param string $N The username as present in the database
 *
 * @return void
 */
function display_account_form($A,$U="",$T="",$S="",$E="",$H="",$P="",$C="",$R="",
		$L="",$HP="",$I="",$K="",$PK="",$J="",$CN="",$UN="",$ON="",$UID=0,$N="") {
	global $SUPPORTED_LANGS;

	include("account_edit_form.php");
	return;
}

/**
 * Process information given to new/edit account form
 *
 * @global array $SUPPORTED_LANGS Languages that are supported by the AUR
 * @param string $TYPE Either "edit" for editing or "new" for registering an account
 * @param string $A Form to use, either UpdateAccount or NewAccount
 * @param string $U The username for the account
 * @param string $T The account type for the user
 * @param string $S Whether or not the account is suspended
 * @param string $E The e-mail address for the user
 * @param string $H Whether or not the e-mail address should be hidden
 * @param string $P The password for the user
 * @param string $C The confirmed password for the user
 * @param string $R The real name of the user
 * @param string $L The language preference of the user
 * @param string $HP The homepage of the displayed user
 * @param string $I The IRC nickname of the user
 * @param string $K The PGP fingerprint of the user
 * @param string $PK The list of public SSH keys
 * @param string $J The inactivity status of the user
 * @param string $CN Whether to notify of new comments
 * @param string $UN Whether to notify of package updates
 * @param string $ON Whether to notify of ownership changes
 * @param string $UID The user ID of the modified account
 * @param string $N The username as present in the database
 *
 * @return array Boolean indicating success and message to be printed
 */
function process_account_form($TYPE,$A,$U="",$T="",$S="",$E="",$H="",$P="",$C="",
		$R="",$L="",$HP="",$I="",$K="",$PK="",$J="",$CN="",$UN="",$ON="",$UID=0,$N="") {
	global $SUPPORTED_LANGS;

	$error = '';
	$message = '';

	if (is_ipbanned()) {
		$error = __('Account registration has been disabled ' .
					'for your IP address, probably due ' .
					'to sustained spam attacks. Sorry for the ' .
					'inconvenience.');
	}

	$dbh = DB::connect();

	if(isset($_COOKIE['AURSID'])) {
		$editor_user = uid_from_sid($_COOKIE['AURSID']);
	}
	else {
		$editor_user = null;
	}

	if (empty($E) || empty($U)) {
		$error = __("Missing a required field.");
	}

	if ($TYPE != "new" && !$UID) {
		$error = __("Missing User ID");
	}

	if (!$error && !valid_username($U)) {
		$length_min = config_get_int('options', 'username_min_len');
		$length_max = config_get_int('options', 'username_max_len');

		$error = __("The username is invalid.") . "<ul>\n"
			. "<li>" . __("It must be between %s and %s characters long", $length_min, $length_max)
			. "</li>"
			. "<li>" . __("Start and end with a letter or number") . "</li>"
			. "<li>" . __("Can contain only one period, underscore or hyphen.")
			. "</li>\n</ul>";
	}

	if (!$error && $P && $C && ($P != $C)) {
		$error = __("Password fields do not match.");
	}
	if (!$error && $P != '' && !good_passwd($P)) {
		$length_min = config_get_int('options', 'passwd_min_len');
		$error = __("Your password must be at least %s characters.",
			$length_min);
	}

	if (!$error && !valid_email($E)) {
		$error = __("The email address is invalid.");
	}

	if (!$error && $K != '' && !valid_pgp_fingerprint($K)) {
		$error = __("The PGP key fingerprint is invalid.");
	}

	if (!$error && !empty($PK)) {
		$ssh_keys = array_filter(array_map('trim', explode("\n", $PK)));
		$ssh_fingerprints = array();

		foreach ($ssh_keys as &$ssh_key) {
			if (!valid_ssh_pubkey($ssh_key)) {
				$error = __("The SSH public key is invalid.");
				break;
			}

			$ssh_fingerprint = ssh_key_fingerprint($ssh_key);
			if (!$ssh_fingerprint) {
				$error = __("The SSH public key is invalid.");
				break;
			}

			$tokens = explode(" ", $ssh_key);
			$ssh_key = $tokens[0] . " " . $tokens[1];

			$ssh_fingerprints[] = $ssh_fingerprint;
		}

		/*
		 * Destroy last reference to prevent accidentally overwriting
		 * an array element.
		 */
		unset($ssh_key);
	}

	if (isset($_COOKIE['AURSID'])) {
		$atype = account_from_sid($_COOKIE['AURSID']);
		if (($atype == "User" && $T > 1) || ($atype == "Trusted User" && $T > 2)) {
			$error = __("Cannot increase account permissions.");
		}
	}

	if (!$error && !array_key_exists($L, $SUPPORTED_LANGS)) {
		$error = __("Language is not currently supported.");
	}
	if (!$error) {
		/*
		 * Check whether the user name is available.
		 * TODO: Fix race condition.
		 */
		$q = "SELECT COUNT(*) AS CNT FROM Users ";
		$q.= "WHERE Username = " . $dbh->quote($U);
		if ($TYPE == "edit") {
			$q.= " AND ID != ".intval($UID);
		}
		$result = $dbh->query($q);
		$row = $result->fetch(PDO::FETCH_NUM);

		if ($row[0]) {
			$error = __("The username, %s%s%s, is already in use.",
				"<strong>", htmlspecialchars($U,ENT_QUOTES), "</strong>");
		}
	}
	if (!$error) {
		/*
		 * Check whether the e-mail address is available.
		 * TODO: Fix race condition.
		 */
		$q = "SELECT COUNT(*) AS CNT FROM Users ";
		$q.= "WHERE Email = " . $dbh->quote($E);
		if ($TYPE == "edit") {
			$q.= " AND ID != ".intval($UID);
		}
		$result = $dbh->query($q);
		$row = $result->fetch(PDO::FETCH_NUM);

		if ($row[0]) {
			$error = __("The address, %s%s%s, is already in use.",
					"<strong>", htmlspecialchars($E,ENT_QUOTES), "</strong>");
		}
	}
	if (!$error && count($ssh_keys) > 0) {
		/*
		 * Check whether any of the SSH public keys is already in use.
		 * TODO: Fix race condition.
		 */
		$q = "SELECT Fingerprint FROM SSHPubKeys ";
		$q.= "WHERE Fingerprint IN (";
		$q.= implode(',', array_map(array($dbh, 'quote'), $ssh_fingerprints));
		$q.= ")";
		if ($TYPE == "edit") {
			$q.= " AND UserID != " . intval($UID);
		}
		$result = $dbh->query($q);
		$row = $result->fetch(PDO::FETCH_NUM);

		if ($row) {
			$error = __("The SSH public key, %s%s%s, is already in use.",
					"<strong>", htmlspecialchars($row[0], ENT_QUOTES), "</strong>");
		}
	}

	if ($error) {
		$message = "<ul class='errorlist'><li>".$error."</li></ul>\n";
		return array(false, $message);
	}

	if ($TYPE == "new") {
		/* Create an unprivileged user. */
		$salt = generate_salt();
		if (empty($P)) {
			$send_resetkey = true;
			$email = $E;
		} else {
			$send_resetkey = false;
			$P = salted_hash($P, $salt);
		}
		$U = $dbh->quote($U);
		$E = $dbh->quote($E);
		$P = $dbh->quote($P);
		$salt = $dbh->quote($salt);
		$R = $dbh->quote($R);
		$L = $dbh->quote($L);
		$HP = $dbh->quote($HP);
		$I = $dbh->quote($I);
		$K = $dbh->quote(str_replace(" ", "", $K));
		$q = "INSERT INTO Users (AccountTypeID, Suspended, ";
		$q.= "InactivityTS, Username, Email, Passwd, Salt, ";
		$q.= "RealName, LangPreference, Homepage, IRCNick, PGPKey) ";
		$q.= "VALUES (1, 0, 0, $U, $E, $P, $salt, $R, $L, ";
		$q.= "$HP, $I, $K)";
		$result = $dbh->exec($q);
		if (!$result) {
			$message = __("Error trying to create account, %s%s%s.",
					"<strong>", htmlspecialchars($U,ENT_QUOTES), "</strong>");
			return array(false, $message);
		}

		$uid = $dbh->lastInsertId();
		account_set_ssh_keys($uid, $ssh_keys, $ssh_fingerprints);

		$message = __("The account, %s%s%s, has been successfully created.",
				"<strong>", htmlspecialchars($U,ENT_QUOTES), "</strong>");
		$message .= "<p>\n";

		if ($send_resetkey) {
			send_resetkey($email, true);
			$message .= __("A password reset key has been sent to your e-mail address.");
			$message .= "</p>\n";
		} else {
			$message .= __("Click on the Login link above to use your account.");
			$message .= "</p>\n";
		}
	} else {
		/* Modify an existing account. */
		$q = "SELECT InactivityTS FROM Users WHERE ";
		$q.= "ID = " . intval($UID);
		$result = $dbh->query($q);
		$row = $result->fetch(PDO::FETCH_NUM);
		if ($row[0] && $J) {
			$inactivity_ts = $row[0];
		} elseif ($J) {
			$inactivity_ts = time();
		} else {
			$inactivity_ts = 0;
		}

		$q = "UPDATE Users SET ";
		$q.= "Username = " . $dbh->quote($U);
		if ($T) {
			$q.= ", AccountTypeID = ".intval($T);
		}
		if ($S) {
			/* Ensure suspended users can't keep an active session */
			delete_user_sessions($UID);
			$q.= ", Suspended = 1";
		} else {
			$q.= ", Suspended = 0";
		}
		$q.= ", Email = " . $dbh->quote($E);
		if ($H) {
			$q.= ", HideEmail = 1";
		} else {
			$q.= ", HideEmail = 0";
		}
		if ($P) {
			$salt = generate_salt();
			$hash = salted_hash($P, $salt);
			$q .= ", Passwd = '$hash', Salt = '$salt'";
		}
		$q.= ", RealName = " . $dbh->quote($R);
		$q.= ", LangPreference = " . $dbh->quote($L);
		$q.= ", Homepage = " . $dbh->quote($HP);
		$q.= ", IRCNick = " . $dbh->quote($I);
		$q.= ", PGPKey = " . $dbh->quote(str_replace(" ", "", $K));
		$q.= ", InactivityTS = " . $inactivity_ts;
		$q.= ", CommentNotify = " . ($CN ? "1" : "0");
		$q.= ", UpdateNotify = " . ($UN ? "1" : "0");
		$q.= ", OwnershipNotify = " . ($ON ? "1" : "0");
		$q.= " WHERE ID = ".intval($UID);
		$result = $dbh->exec($q);

		$ssh_key_result = account_set_ssh_keys($UID, $ssh_keys, $ssh_fingerprints);

		if ($result === false || $ssh_key_result === false) {
			$message = __("No changes were made to the account, %s%s%s.",
					"<strong>", htmlspecialchars($U,ENT_QUOTES), "</strong>");
		} else {
			$message = __("The account, %s%s%s, has been successfully modified.",
					"<strong>", htmlspecialchars($U,ENT_QUOTES), "</strong>");
		}
	}

	return array(true, $message);
}

/**
 * Display the search results page
 *
 * @param string $O The offset for the results page
 * @param string $SB The column to sort the results page by
 * @param string $U The username search criteria
 * @param string $T The account type search criteria
 * @param string $S Whether the account is suspended search criteria
 * @param string $E The e-mail address search criteria
 * @param string $R The real name search criteria
 * @param string $I The IRC nickname search criteria
 * @param string $K The PGP key fingerprint search criteria
 *
 * @return void
 */
function search_results_page($O=0,$SB="",$U="",$T="",
		$S="",$E="",$R="",$I="",$K="") {

	$HITS_PER_PAGE = 50;
	if ($O) {
		$OFFSET = intval($O);
	} else {
		$OFFSET = 0;
	}
	if ($OFFSET < 0) {
		$OFFSET = 0;
	}
	$search_vars = array();

	$dbh = DB::connect();

	$q = "SELECT Users.*, AccountTypes.AccountType ";
	$q.= "FROM Users, AccountTypes ";
	$q.= "WHERE AccountTypes.ID = Users.AccountTypeID ";
	if ($T == "u") {
		$q.= "AND AccountTypes.ID = 1 ";
		$search_vars[] = "T";
	} elseif ($T == "t") {
		$q.= "AND AccountTypes.ID = 2 ";
		$search_vars[] = "T";
	} elseif ($T == "d") {
		$q.= "AND AccountTypes.ID = 3 ";
		$search_vars[] = "T";
	} elseif ($T == "td") {
		$q.= "AND AccountTypes.ID = 4 ";
		$search_vars[] = "T";
	}
	if ($S) {
		$q.= "AND Users.Suspended = 1 ";
		$search_vars[] = "S";
	}
	if ($U) {
		$U = "%" . addcslashes($U, '%_') . "%";
		$q.= "AND Username LIKE " . $dbh->quote($U) . " ";
		$search_vars[] = "U";
	}
	if ($E) {
		$E = "%" . addcslashes($E, '%_') . "%";
		$q.= "AND Email LIKE " . $dbh->quote($E) . " ";
		$search_vars[] = "E";
	}
	if ($R) {
		$R = "%" . addcslashes($R, '%_') . "%";
		$q.= "AND RealName LIKE " . $dbh->quote($R) . " ";
		$search_vars[] = "R";
	}
	if ($I) {
		$I = "%" . addcslashes($I, '%_') . "%";
		$q.= "AND IRCNick LIKE " . $dbh->quote($I) . " ";
		$search_vars[] = "I";
	}
	if ($K) {
		$K = "%" . addcslashes(str_replace(" ", "", $K), '%_') . "%";
		$q.= "AND PGPKey LIKE " . $dbh->quote($K) . " ";
		$search_vars[] = "K";
	}
	switch ($SB) {
		case 't':
			$q.= "ORDER BY AccountTypeID, Username ";
			break;
		case 'r':
			$q.= "ORDER BY RealName, AccountTypeID ";
			break;
		case 'i':
			$q.= "ORDER BY IRCNick, AccountTypeID ";
			break;
		default:
			$q.= "ORDER BY Username, AccountTypeID ";
			break;
	}
	$search_vars[] = "SB";
	$q.= "LIMIT " . $HITS_PER_PAGE . " OFFSET " . $OFFSET;

	$dbh = DB::connect();

	$result = $dbh->query($q);

	while ($row = $result->fetch(PDO::FETCH_ASSOC)) {
		$userinfo[] = $row;
	}

	include("account_search_results.php");
	return;
}

/**
 * Attempt to login and generate a session
 *
 * @return array Session ID for user, error message if applicable
 */
function try_login() {
	$login_error = "";
	$new_sid = "";
	$userID = null;

	if (!isset($_REQUEST['user']) && !isset($_REQUEST['passwd'])) {
		return array('SID' => '', 'error' => null);
	}

	if (is_ipbanned()) {
		$login_error = __('The login form is currently disabled ' .
						'for your IP address, probably due ' .
						'to sustained spam attacks. Sorry for the ' .
						'inconvenience.');
		return array('SID' => '', 'error' => $login_error);
	}

	$dbh = DB::connect();
	$userID = uid_from_loginname($_REQUEST['user']);

	if (user_suspended($userID)) {
		$login_error = __('Account suspended');
		return array('SID' => '', 'error' => $login_error);
	} elseif (passwd_is_empty($userID)) {
		$login_error = __('Your password has been reset. ' .
			'If you just created a new account, please ' .
			'use the link from the confirmation email ' .
			'to set an initial password. Otherwise, ' .
			'please request a reset key on the %s' .
			'Password Reset%s page.', '<a href="' .
			htmlspecialchars(get_uri('/passreset')) . '">',
			'</a>');
		return array('SID' => '', 'error' => $login_error);
	} elseif (!valid_passwd($userID, $_REQUEST['passwd'])) {
		$login_error = __("Bad username or password.");
		return array('SID' => '', 'error' => $login_error);
	}

	$logged_in = 0;
	$num_tries = 0;

	/* Generate a session ID and store it. */
	while (!$logged_in && $num_tries < 5) {
		$session_limit = config_get_int('options', 'max_sessions_per_user');
		if ($session_limit) {
			/*
			 * Delete all user sessions except the
			 * last ($session_limit - 1).
			 */
			$q = "DELETE s.* FROM Sessions s ";
			$q.= "LEFT JOIN (SELECT SessionID FROM Sessions ";
			$q.= "WHERE UsersId = " . $userID . " ";
			$q.= "ORDER BY LastUpdateTS DESC ";
			$q.= "LIMIT " . ($session_limit - 1) . ") q ";
			$q.= "ON s.SessionID = q.SessionID ";
			$q.= "WHERE s.UsersId = " . $userID . " ";
			$q.= "AND q.SessionID IS NULL;";
			$dbh->query($q);
		}

		$new_sid = new_sid();
		$q = "INSERT INTO Sessions (UsersID, SessionID, LastUpdateTS)"
		  ." VALUES (" . $userID . ", '" . $new_sid . "', " . strval(time()) . ")";
		$result = $dbh->exec($q);

		/* Query will fail if $new_sid is not unique. */
		if ($result) {
			$logged_in = 1;
			break;
		}

		$num_tries++;
	}

	if (!$logged_in) {
		$login_error = __('An error occurred trying to generate a user session.');
		return array('SID' => $new_sid, 'error' => $login_error);
	}

	$q = "UPDATE Users SET LastLogin = " . strval(time()) . ", ";
	$q.= "LastLoginIPAddress = " . $dbh->quote($_SERVER['REMOTE_ADDR']) . " ";
	$q.= "WHERE ID = $userID";
	$dbh->exec($q);

	/* Set the SID cookie. */
	if (isset($_POST['remember_me']) && $_POST['remember_me'] == "on") {
		/* Set cookies for 30 days. */
		$timeout = config_get_int('options', 'persistent_cookie_timeout');
		$cookie_time = time() + $timeout;

		/* Set session for 30 days. */
		$q = "UPDATE Sessions SET LastUpdateTS = $cookie_time ";
		$q.= "WHERE SessionID = '$new_sid'";
		$dbh->exec($q);
	} else {
		$cookie_time = 0;
	}

	setcookie("AURSID", $new_sid, $cookie_time, "/", null, !empty($_SERVER['HTTPS']), true);

	$referer = in_request('referer');
	if (strpos($referer, aur_location()) !== 0) {
		$referer = '/';
	}
	header("Location: " . get_uri($referer));
	$login_error = "";
}

/**
 * Determine if the user is using a banned IP address
 *
 * @return bool True if IP address is banned, otherwise false
 */
function is_ipbanned() {
	$dbh = DB::connect();

	$q = "SELECT * FROM Bans WHERE IPAddress = " . $dbh->quote(ip2long($_SERVER['REMOTE_ADDR']));
	$result = $dbh->query($q);

	return ($result->fetchColumn() ? true : false);
}

/**
 * Validate a username against a collection of rules
 *
 * The username must be longer or equal to the configured minimum length. It
 * must be shorter or equal to the configured maximum length. It must start and
 * end with either a letter or a number. It can contain one period, hypen, or
 * underscore. Returns boolean of whether name is valid.
 *
 * @param string $user Username to validate
 *
 * @return bool True if username meets criteria, otherwise false
 */
function valid_username($user) {
	$length_min = config_get_int('options', 'username_min_len');
	$length_max = config_get_int('options', 'username_max_len');

	if (strlen($user) < $length_min || strlen($user) > $length_max) {
		return false;
	} else if (!preg_match("/^[a-z0-9]+[.\-_]?[a-z0-9]+$/Di", $user)) {
		return false;
	}

	return true;
}

/**
 * Determine if a user already has a proposal open about themselves
 *
 * @param string $user Username to checkout for open proposal
 *
 * @return bool True if there is an open proposal about the user, otherwise false
 */
function open_user_proposals($user) {
	$dbh = DB::connect();
	$q = "SELECT * FROM TU_VoteInfo WHERE User = " . $dbh->quote($user) . " ";
	$q.= "AND End > " . strval(time());
	$result = $dbh->query($q);

	return ($result->fetchColumn() ? true : false);
}

/**
 * Add a new Trusted User proposal to the database
 *
 * @param string $agenda The agenda of the vote
 * @param string $user The use the vote is about
 * @param int $votelength The length of time for the vote to last
 * @param string $submitteruid The user ID of the individual who submitted the proposal
 *
 * @return void
 */
function add_tu_proposal($agenda, $user, $votelength, $quorum, $submitteruid) {
	$dbh = DB::connect();

	$q = "SELECT COUNT(*) FROM Users WHERE (AccountTypeID = 2 OR AccountTypeID = 4)";
	$result = $dbh->query($q);
	$row = $result->fetch(PDO::FETCH_NUM);
	$active_tus = $row[0];

	$q = "INSERT INTO TU_VoteInfo (Agenda, User, Submitted, End, Quorum, ";
	$q.= "SubmitterID, ActiveTUs) VALUES ";
	$q.= "(" . $dbh->quote($agenda) . ", " . $dbh->quote($user) . ", ";
	$q.= strval(time()) . ", " . strval(time()) . " + " . $dbh->quote($votelength);
	$q.= ", " . $dbh->quote($quorum) . ", " . $submitteruid . ", ";
	$q.= $active_tus . ")";
	$result = $dbh->exec($q);
}

/**
 * Add a reset key to the database for a specified user
 *
 * @param string $resetkey A password reset key to be stored in database
 * @param string $uid The user ID to store the reset key for
 *
 * @return void
 */
function create_resetkey($resetkey, $uid) {
	$dbh = DB::connect();
	$q = "UPDATE Users ";
	$q.= "SET ResetKey = '" . $resetkey . "' ";
	$q.= "WHERE ID = " . $uid;
	$dbh->exec($q);
}

/**
 * Send a reset key to a specific e-mail address
 *
 * @param string $email E-mail address of the user resetting their password
 * @param bool $welcome Whether to use the welcome message
 *
 * @return void
 */
function send_resetkey($email, $welcome=false) {
	$uid = uid_from_email($email);
	if ($uid == null) {
		return;
	}

	/* We (ab)use new_sid() to get a random 32 characters long string. */
	$resetkey = new_sid();
	create_resetkey($resetkey, $uid);

	/* Send e-mail with confirmation link. */
	notify(array($welcome ? 'welcome' : 'send-resetkey', $uid));
}

/**
 * Change a user's password in the database if reset key and e-mail are correct
 *
 * @param string $hash New MD5 hash of a user's password
 * @param string $salt New salt for the user's password
 * @param string $resetkey Code e-mailed to a user to reset a password
 * @param string $email E-mail address of the user resetting their password
 *
 * @return string|void Redirect page if successful, otherwise return error message
 */
function password_reset($hash, $salt, $resetkey, $email) {
	$dbh = DB::connect();
	$q = "UPDATE Users ";
	$q.= "SET Passwd = '$hash', ";
	$q.= "Salt = '$salt', ";
	$q.= "ResetKey = '' ";
	$q.= "WHERE ResetKey != '' ";
	$q.= "AND ResetKey = " . $dbh->quote($resetkey) . " ";
	$q.= "AND Email = " . $dbh->quote($email);
	$result = $dbh->exec($q);

	if (!$result) {
		$error = __('Invalid e-mail and reset key combination.');
		return $error;
	} else {
		header('Location: ' . get_uri('/passreset/') . '?step=complete');
		exit();
	}
}

/**
 * Determine if the password is longer than the minimum length
 *
 * @param string $passwd The password to check
 *
 * @return bool True if longer than minimum length, otherwise false
 */
function good_passwd($passwd) {
	$length_min = config_get_int('options', 'passwd_min_len');
	return (strlen($passwd) >= $length_min);
}

/**
 * Determine if the password is correct and salt it if it hasn't been already
 *
 * @param string $userID The user ID to check the password against
 * @param string $passwd The password the visitor sent
 *
 * @return bool True if password was correct and properly salted, otherwise false
 */
function valid_passwd($userID, $passwd) {
	$dbh = DB::connect();
	if ($passwd == "") {
		return false;
	}

	/* Get salt for this user. */
	$salt = get_salt($userID);
	if ($salt) {
		$q = "SELECT ID FROM Users ";
		$q.= "WHERE ID = " . $userID . " ";
		$q.= "AND Passwd = " . $dbh->quote(salted_hash($passwd, $salt));
		$result = $dbh->query($q);
		if (!$result) {
			return false;
		}

		$row = $result->fetch(PDO::FETCH_NUM);
		return ($row[0] > 0);
	} else {
		/* Check password without using salt. */
		$q = "SELECT ID FROM Users ";
		$q.= "WHERE ID = " . $userID . " ";
		$q.= "AND Passwd = " . $dbh->quote(md5($passwd));
		$result = $dbh->query($q);
		if (!$result) {
			return false;
		}

		$row = $result->fetch(PDO::FETCH_NUM);
		if (!$row[0]) {
			return false;
		}

		/* Password correct, but salt it first! */
		if (!save_salt($userID, $passwd)) {
			trigger_error("Unable to salt user's password;" .
				" ID " . $userID, E_USER_WARNING);
			return false;
		}

		return true;
	}
}

/**
 * Determine if a user's password is empty
 *
 * @param string $uid The user ID to check for an empty password
 *
 * @return bool True if the user's password is empty, otherwise false
 */
function passwd_is_empty($uid) {
	$dbh = DB::connect();

	$q = "SELECT * FROM Users WHERE ID = " . $dbh->quote($uid) . " ";
	$q .= "AND Passwd = " . $dbh->quote('');
	$result = $dbh->query($q);

	if ($result->fetchColumn()) {
		return true;
	} else {
		return false;
	}
}

/**
 * Determine if the PGP key fingerprint is valid (must be 40 hexadecimal digits)
 *
 * @param string $fingerprint PGP fingerprint to check if valid
 *
 * @return bool True if the fingerprint is 40 hexadecimal digits, otherwise false
 */
function valid_pgp_fingerprint($fingerprint) {
	$fingerprint = str_replace(" ", "", $fingerprint);
	return (strlen($fingerprint) == 40 && ctype_xdigit($fingerprint));
}

/**
 * Determine if the SSH public key is valid
 *
 * @param string $pubkey SSH public key to check
 *
 * @return bool True if the SSH public key is valid, otherwise false
 */
function valid_ssh_pubkey($pubkey) {
	$valid_prefixes = array(
		"ssh-rsa", "ssh-dss", "ecdsa-sha2-nistp256",
		"ecdsa-sha2-nistp384", "ecdsa-sha2-nistp521", "ssh-ed25519"
	);

	$has_valid_prefix = false;
	foreach ($valid_prefixes as $prefix) {
		if (strpos($pubkey, $prefix . " ") === 0) {
			$has_valid_prefix = true;
			break;
		}
	}
	if (!$has_valid_prefix) {
		return false;
	}

	$tokens = explode(" ", $pubkey);
	if (empty($tokens[1])) {
		return false;
	}

	return (base64_encode(base64_decode($tokens[1], true)) == $tokens[1]);
}

/**
 * Determine if the user account has been suspended
 *
 * @param string $id The ID of user to check if suspended
 *
 * @return bool True if the user is suspended, otherwise false
 */
function user_suspended($id) {
	$dbh = DB::connect();
	if (!$id) {
		return false;
	}
	$q = "SELECT Suspended FROM Users WHERE ID = " . $id;
	$result = $dbh->query($q);
	if ($result) {
		$row = $result->fetch(PDO::FETCH_NUM);
		if ($row[0]) {
			return true;
		}
	}
	return false;
}

/**
 * Delete a specified user account from the database
 *
 * @param int $id The user ID of the account to be deleted
 *
 * @return void
 */
function user_delete($id) {
	$dbh = DB::connect();
	$id = intval($id);

	/*
	 * These are normally already taken care of by propagation constraints
	 * but it is better to be explicit here.
	 */
	$fields_delete = array(
		array("Sessions", "UsersID"),
		array("PackageVotes", "UsersID"),
		array("PackageNotifications", "UsersID")
	);

	$fields_set_null = array(
		array("PackageBases", "SubmitterUID"),
		array("PackageBases", "MaintainerUID"),
		array("PackageBases", "SubmitterUID"),
		array("PackageComments", "UsersID"),
		array("PackageComments", "DelUsersID"),
		array("PackageRequests", "UsersID"),
		array("TU_VoteInfo", "SubmitterID"),
		array("TU_Votes", "UserID")
	);

	foreach($fields_delete as list($table, $field)) {
		$q = "DELETE FROM " . $table . " ";
		$q.= "WHERE " . $field . " = " . $id;
		$dbh->query($q);
	}

	foreach($fields_set_null as list($table, $field)) {
		$q = "UPDATE " . $table . " SET " . $field . " = NULL ";
		$q.= "WHERE " . $field . " = " . $id;
		$dbh->query($q);
	}

	$q = "DELETE FROM Users WHERE ID = " . $id;
	$dbh->query($q);
	return;
}

/**
 * Remove the session from the database on logout
 *
 * @param string $sid User's session ID
 *
 * @return void
 */
function delete_session_id($sid) {
	$dbh = DB::connect();

	$q = "DELETE FROM Sessions WHERE SessionID = " . $dbh->quote($sid);
	$dbh->query($q);
}

/**
 * Remove all sessions belonging to a particular user
 *
 * @param int $uid ID of user to remove all sessions for
 *
 * @return void
 */
function delete_user_sessions($uid) {
	$dbh = DB::connect();

	$q = "DELETE FROM Sessions WHERE UsersID = " . intval($uid);
	$dbh->exec($q);
}

/**
 * Remove sessions from the database that have exceed the timeout
 *
 * @return void
 */
function clear_expired_sessions() {
	$dbh = DB::connect();

	$timeout = config_get_int('options', 'login_timeout');
	$q = "DELETE FROM Sessions WHERE LastUpdateTS < (" . strval(time()) . " - " . $timeout . ")";
	$dbh->query($q);

	return;
}

/**
 * Get account details for a specific user
 *
 * @param string $uid The User ID of account to get information for
 * @param string $username The username of the account to get for
 *
 * @return array Account details for the specified user
 */
function account_details($uid, $username) {
	$dbh = DB::connect();
	$q = "SELECT Users.*, AccountTypes.AccountType ";
	$q.= "FROM Users, AccountTypes ";
	$q.= "WHERE AccountTypes.ID = Users.AccountTypeID ";
	if (!empty($uid)) {
		$q.= "AND Users.ID = ".intval($uid);
	} else {
		$q.= "AND Users.Username = " . $dbh->quote($username);
	}
	$result = $dbh->query($q);

	if ($result) {
		$row = $result->fetch(PDO::FETCH_ASSOC);
	}

	return $row;
}

/**
 * Determine if a user has already voted on a specific proposal
 *
 * @param string $voteid The ID of the Trusted User proposal
 * @param string $uid The ID to check if the user already voted
 *
 * @return bool True if the user has already voted, otherwise false
 */
function tu_voted($voteid, $uid) {
	$dbh = DB::connect();

	$q = "SELECT COUNT(*) FROM TU_Votes ";
	$q.= "WHERE VoteID = " . intval($voteid) . " AND UserID = " . intval($uid);
	$result = $dbh->query($q);
	if ($result->fetchColumn() > 0) {
		return true;
	}
	else {
		return false;
	}
}

/**
 * Get all current Trusted User proposals from the database
 *
 * @param string $order Ascending or descending order for the proposal listing
 *
 * @return array The details for all current Trusted User proposals
 */
function current_proposal_list($order) {
	$dbh = DB::connect();

	$q = "SELECT * FROM TU_VoteInfo WHERE End > " . time() . " ORDER BY Submitted " . $order;
	$result = $dbh->query($q);

	$details = array();
	while ($row = $result->fetch(PDO::FETCH_ASSOC)) {
		$details[] = $row;
	}

	return $details;
}

/**
 * Get a subset of all past Trusted User proposals from the database
 *
 * @param string $order Ascending or descending order for the proposal listing
 * @param string $lim The number of proposals to list with the offset
 *
 * @return array The details for the subset of past Trusted User proposals
 */
function past_proposal_list($order, $lim) {
	$dbh = DB::connect();

	$q = "SELECT * FROM TU_VoteInfo WHERE End < " . time() . " ORDER BY Submitted " . $order . $lim;
	$result = $dbh->query($q);

	$details = array();
	while ($row = $result->fetch(PDO::FETCH_ASSOC)) {
		$details[] = $row;
	}

	return $details;
}

/**
 * Get the vote ID of the last vote of all Trusted Users
 *
 * @return array The vote ID of the last vote of each Trusted User
 */
function last_votes_list() {
	$dbh = DB::connect();

	$q = "SELECT UserID, MAX(VoteID) AS LastVote FROM TU_Votes, ";
	$q .= "TU_VoteInfo, Users WHERE TU_VoteInfo.ID = TU_Votes.VoteID AND ";
	$q .= "TU_VoteInfo.End < " . strval(time()) . " AND ";
	$q .= "Users.ID = TU_Votes.UserID AND (Users.AccountTypeID = 2 OR Users.AccountTypeID = 4) ";
	$q .= "GROUP BY UserID ORDER BY LastVote DESC, UserName ASC";
	$result = $dbh->query($q);

	$details = array();
	while ($row = $result->fetch(PDO::FETCH_ASSOC)) {
		$details[] = $row;
	}

	return $details;
}

/**
 * Determine the total number of Trusted User proposals
 *
 * @return string The total number of Trusted User proposals
 */
function proposal_count() {
	$dbh = DB::connect();
	$q = "SELECT COUNT(*) FROM TU_VoteInfo";
	$result = $dbh->query($q);
	$row = $result->fetch(PDO::FETCH_NUM);

	return $row[0];
}

/**
 * Get all details related to a specific vote from the database
 *
 * @param string $voteid The ID of the Trusted User proposal
 *
 * @return array All stored details for a specific vote
 */
function vote_details($voteid) {
	$dbh = DB::connect();

	$q = "SELECT * FROM TU_VoteInfo ";
	$q.= "WHERE ID = " . intval($voteid);

	$result = $dbh->query($q);
	$row = $result->fetch(PDO::FETCH_ASSOC);

	return $row;
}

/**
 * Get an alphabetical list of users who voted for a proposal with HTML links
 *
 * @param string $voteid The ID of the Trusted User proposal
 *
 * @return array All users who voted for a specific proposal
 */
function voter_list($voteid) {
	$dbh = DB::connect();

	$whovoted = array();

	$q = "SELECT tv.UserID,U.Username ";
	$q.= "FROM TU_Votes tv, Users U ";
	$q.= "WHERE tv.VoteID = " . intval($voteid);
	$q.= " AND tv.UserID = U.ID ";
	$q.= "ORDER BY Username";

	$result = $dbh->query($q);
	if ($result) {
		while ($row = $result->fetch(PDO::FETCH_ASSOC)) {
			$whovoted[] = $row['Username'];
		}
	}
	return $whovoted;
}

/**
 * Cast a vote for a specific user proposal
 *
 * @param string $voteid The ID of the proposal being voted on
 * @param string $uid The user ID of the individual voting
 * @param string $vote Vote position, either "Yes", "No", or "Abstain"
 * @param int $newtotal The total number of votes after the user has voted
 *
 * @return void
 */
function cast_proposal_vote($voteid, $uid, $vote, $newtotal) {
	$dbh = DB::connect();

	$q = "UPDATE TU_VoteInfo SET " . $vote . " = (" . $newtotal . ") WHERE ID = " . $voteid;
	$result = $dbh->exec($q);

	$q = "INSERT INTO TU_Votes (VoteID, UserID) VALUES (" . intval($voteid) . ", " . intval($uid) . ")";
	$result = $dbh->exec($q);
}

/**
 * Verify a user has the proper permissions to edit an account
 *
 * @param array $acctinfo User account information for edited account
 *
 * @return bool True if permission to edit the account, otherwise false
 */
function can_edit_account($acctinfo) {
	if ($acctinfo['AccountType'] == 'Developer' ||
	    $acctinfo['AccountType'] == 'Trusted User & Developer') {
		return has_credential(CRED_ACCOUNT_EDIT_DEV);
	}

	$uid = $acctinfo['ID'];
	return has_credential(CRED_ACCOUNT_EDIT, array($uid));
}

/*
 * Compute the fingerprint of an SSH key.
 *
 * @param string $ssh_key The SSH public key to retrieve the fingerprint for
 *
 * @return string The SSH key fingerprint
 */
function ssh_key_fingerprint($ssh_key) {
	$tmpfile = tempnam(sys_get_temp_dir(), "aurweb");
	file_put_contents($tmpfile, $ssh_key);

	/*
	 * The -l option of ssh-keygen can be used to show the fingerprint of
	 * the specified public key file. Expected output format:
	 *
	 *     2048 SHA256:uBBTXmCNjI2CnLfkuz9sG8F+e9/T4C+qQQwLZWIODBY user@host (RSA)
	 *
	 * ... where 2048 is the key length, the second token is the actual
	 * fingerprint, followed by the key comment and the key type.
	 */

	$cmd = "/usr/bin/ssh-keygen -l -f " . escapeshellarg($tmpfile);
	exec($cmd, $out, $ret);
	if ($ret !== 0 || count($out) !== 1) {
		return false;
	}

	unlink($tmpfile);

	$tokens = explode(' ', $out[0]);
	if (count($tokens) < 4) {
		return false;
	}

	$tokens = explode(':', $tokens[1]);
	if (count($tokens) != 2 || $tokens[0] != 'SHA256') {
		return false;
	}

	return $tokens[1];
}

/*
 * Get the SSH public keys associated with an account.
 *
 * @param int $uid The user ID of the account to retrieve the keys for.
 *
 * @return array An array representing the keys
 */
function account_get_ssh_keys($uid) {
	$dbh = DB::connect();
	$q = "SELECT PubKey FROM SSHPubKeys WHERE UserID = " . intval($uid);
	$result = $dbh->query($q);

	if ($result) {
		return $result->fetchAll(PDO::FETCH_COLUMN, 0);
	} else {
		return array();
	}
}

/*
 * Set the SSH public keys associated with an account.
 *
 * @param int $uid The user ID of the account to assign the keys to.
 * @param array $ssh_keys The SSH public keys.
 * @param array $ssh_fingerprints The corresponding SSH key fingerprints.
 *
 * @return bool Boolean flag indicating success or failure.
 */
function account_set_ssh_keys($uid, $ssh_keys, $ssh_fingerprints) {
	$dbh = DB::connect();

	$q = sprintf("DELETE FROM SSHPubKeys WHERE UserID = %d", $uid);
	$dbh->exec($q);

	$ssh_fingerprint = reset($ssh_fingerprints);
	foreach ($ssh_keys as $ssh_key) {
		$q = sprintf(
			"INSERT INTO SSHPubKeys (UserID, Fingerprint, PubKey) " .
			"VALUES (%d, %s, %s)", $uid,
			$dbh->quote($ssh_fingerprint), $dbh->quote($ssh_key)
		);
		$dbh->exec($q);
		$ssh_fingerprint = next($ssh_fingerprints);
	}

	return true;
}

/*
 * Invoke the email notification script.
 *
 * @param string $params Command line parameters for the script.
 *
 * @return void
 */
function notify($params) {
	$cmd = config_get('notifications', 'notify-cmd');
	foreach ($params as $param) {
		$cmd .= ' ' . escapeshellarg($param);
	}

	$descspec = array(
		0 => array('pipe', 'r'),
		1 => array('pipe', 'w'),
		2 => array('pipe', 'w')
	);

	$p = proc_open($cmd, $descspec, $pipes);

	if (!is_resource($p)) {
		return false;
	}

	fclose($pipes[0]);
	fclose($pipes[1]);
	fclose($pipes[2]);

	return proc_close($p);
}
