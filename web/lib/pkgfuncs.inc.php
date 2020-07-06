<?php

include_once("pkgbasefuncs.inc.php");

/**
 * Determine if the user can delete a specific package comment
 *
 * Only the comment submitter, Trusted Users, and Developers can delete
 * comments. This function is used for the backend side of comment deletion.
 *
 * @param string $comment_id The comment ID in the database
 *
 * @return bool True if the user can delete the comment, otherwise false
 */
function can_delete_comment($comment_id=0) {
	$dbh = DB::connect();

	$q = "SELECT UsersID FROM PackageComments ";
	$q.= "WHERE ID = " . intval($comment_id);
	$result = $dbh->query($q);

	if (!$result) {
		return false;
	}

	$uid = $result->fetch(PDO::FETCH_COLUMN, 0);

	return has_credential(CRED_COMMENT_DELETE, array($uid));
}

/**
 * Determine if the user can delete a specific package comment using an array
 *
 * Only the comment submitter, Trusted Users, and Developers can delete
 * comments. This function is used for the frontend side of comment deletion.
 *
 * @param array $comment All database information relating a specific comment
 *
 * @return bool True if the user can delete the comment, otherwise false
 */
function can_delete_comment_array($comment) {
	return has_credential(CRED_COMMENT_DELETE, array($comment['UsersID']));
}

/**
 * Determine if the user can edit a specific package comment
 *
 * Only the comment submitter, Trusted Users, and Developers can edit
 * comments. This function is used for the backend side of comment editing.
 *
 * @param string $comment_id The comment ID in the database
 *
 * @return bool True if the user can edit the comment, otherwise false
 */
function can_edit_comment($comment_id=0) {
	$dbh = DB::connect();

	$q = "SELECT UsersID FROM PackageComments ";
	$q.= "WHERE ID = " . intval($comment_id);
	$result = $dbh->query($q);

	if (!$result) {
		return false;
	}

	$uid = $result->fetch(PDO::FETCH_COLUMN, 0);

	return has_credential(CRED_COMMENT_EDIT, array($uid));
}

/**
 * Determine if the user can edit a specific package comment using an array
 *
 * Only the comment submitter, Trusted Users, and Developers can edit
 * comments. This function is used for the frontend side of comment editing.
 *
 * @param array $comment All database information relating a specific comment
 *
 * @return bool True if the user can edit the comment, otherwise false
 */
function can_edit_comment_array($comment) {
	return has_credential(CRED_COMMENT_EDIT, array($comment['UsersID']));
}

/**
 * Determine if the user can pin a specific package comment
 *
 * Only the Package Maintainer, Package Co-maintainers, Trusted Users, and
 * Developers can pin comments. This function is used for the backend side of
 * comment pinning.
 *
 * @param string $comment_id The comment ID in the database
 *
 * @return bool True if the user can pin the comment, otherwise false
 */
function can_pin_comment($comment_id=0) {
	$dbh = DB::connect();

	$q = "SELECT MaintainerUID FROM PackageBases AS pb ";
	$q.= "LEFT JOIN PackageComments AS pc ON pb.ID = pc.PackageBaseID ";
	$q.= "WHERE pc.ID = " . intval($comment_id) . " ";
	$q.= "UNION ";
	$q.= "SELECT pcm.UsersID FROM PackageComaintainers AS pcm ";
	$q.= "LEFT JOIN PackageComments AS pc ";
	$q.= "ON pcm.PackageBaseID = pc.PackageBaseID ";
	$q.= "WHERE pc.ID = " . intval($comment_id);
	$result = $dbh->query($q);

	if (!$result) {
		return false;
	}

	$uids = $result->fetchAll(PDO::FETCH_COLUMN, 0);

	return has_credential(CRED_COMMENT_PIN, $uids);
}

/**
 * Determine if the user can edit a specific package comment using an array
 *
 * Only the Package Maintainer, Package Co-maintainers, Trusted Users, and
 * Developers can pin comments. This function is used for the frontend side of
 * comment pinning.
 *
 * @param array $comment All database information relating a specific comment
 *
 * @return bool True if the user can edit the comment, otherwise false
 */
function can_pin_comment_array($comment) {
	return can_pin_comment($comment['ID']);
}

/**
 * Check to see if the package name already exists in the database
 *
 * @param string $name The package name to check
 *
 * @return string|void Package name if it already exists
 */
function pkg_from_name($name="") {
	if (!$name) {return NULL;}
	$dbh = DB::connect();
	$q = "SELECT ID FROM Packages ";
	$q.= "WHERE Name = " . $dbh->quote($name);
	$result = $dbh->query($q);
	if (!$result) {
		return;
	}
	$row = $result->fetch(PDO::FETCH_NUM);
	if ($row) {
		return $row[0];
	}
}

/**
 * Get licenses for a specific package
 *
 * @param int $pkgid The package to get licenses for
 *
 * @return array All licenses for the package
 */
function pkg_licenses($pkgid) {
	$pkgid = intval($pkgid);
	if (!$pkgid) {
		return array();
	}
	$q = "SELECT l.Name FROM Licenses l ";
	$q.= "INNER JOIN PackageLicenses pl ON pl.LicenseID = l.ID ";
	$q.= "WHERE pl.PackageID = ". $pkgid;
	$ttl = config_get_int('options', 'cache_pkginfo_ttl');
	$rows = db_cache_result($q, 'licenses:' . $pkgid, PDO::FETCH_NUM, $ttl);
	return array_map(function ($x) { return $x[0]; }, $rows);
}

/**
 * Get package groups for a specific package
 *
 * @param int $pkgid The package to get groups for
 *
 * @return array All package groups for the package
 */
function pkg_groups($pkgid) {
	$pkgid = intval($pkgid);
	if (!$pkgid) {
		return array();
	}
	$q = "SELECT g.Name FROM `Groups` g ";
	$q.= "INNER JOIN PackageGroups pg ON pg.GroupID = g.ID ";
	$q.= "WHERE pg.PackageID = ". $pkgid;
	$ttl = config_get_int('options', 'cache_pkginfo_ttl');
	$rows = db_cache_result($q, 'groups:' . $pkgid, PDO::FETCH_NUM, $ttl);
	return array_map(function ($x) { return $x[0]; }, $rows);
}

/**
 * Get providers for a specific package
 *
 * @param string $name The name of the "package" to get providers for
 *
 * @return array The IDs and names of all providers of the package
 */
function pkg_providers($name) {
	$dbh = DB::connect();
	$q = "SELECT p.ID, p.Name FROM Packages p ";
	$q.= "WHERE p.Name = " . $dbh->quote($name) . " ";
	$q.= "UNION ";
	$q.= "SELECT p.ID, p.Name FROM Packages p ";
	$q.= "LEFT JOIN PackageRelations pr ON pr.PackageID = p.ID ";
	$q.= "LEFT JOIN RelationTypes rt ON rt.ID = pr.RelTypeID ";
	$q.= "WHERE (rt.Name = 'provides' ";
	$q.= "AND pr.RelName = " . $dbh->quote($name) . ")";
	$q.= "UNION ";
	$q.= "SELECT 0, Name FROM OfficialProviders ";
	$q.= "WHERE Provides = " . $dbh->quote($name);
	$ttl = config_get_int('options', 'cache_pkginfo_ttl');
	return db_cache_result($q, 'providers:' . $name, PDO::FETCH_NUM, $ttl);
}

/**
 * Get package dependencies for a specific package
 *
 * @param int $pkgid The package to get dependencies for
 * @param int $limit An upper bound for the number of packages to retrieve
 *
 * @return array All package dependencies for the package
 */
function pkg_dependencies($pkgid, $limit) {
	$pkgid = intval($pkgid);
	if (!$pkgid) {
		return array();
	}
	$q = "SELECT pd.DepName, dt.Name, pd.DepDesc, ";
	$q.= "pd.DepCondition, pd.DepArch, p.ID ";
	$q.= "FROM PackageDepends pd ";
	$q.= "LEFT JOIN Packages p ON pd.DepName = p.Name ";
	$q.= "LEFT JOIN DependencyTypes dt ON dt.ID = pd.DepTypeID ";
	$q.= "WHERE pd.PackageID = ". $pkgid . " ";
	$q.= "ORDER BY pd.DepName LIMIT " . intval($limit);
	$ttl = config_get_int('options', 'cache_pkginfo_ttl');
	return db_cache_result($q, 'dependencies:' . $pkgid, PDO::FETCH_NUM, $ttl);
}

/**
 * Get package relations for a specific package
 *
 * @param int $pkgid The package to get relations for
 *
 * @return array All package relations for the package
 */
function pkg_relations($pkgid) {
	$pkgid = intval($pkgid);
	if (!$pkgid) {
		return array();
	}
	$q = "SELECT pr.RelName, rt.Name, pr.RelCondition, pr.RelArch, p.ID FROM PackageRelations pr ";
	$q.= "LEFT JOIN Packages p ON pr.RelName = p.Name ";
	$q.= "LEFT JOIN RelationTypes rt ON rt.ID = pr.RelTypeID ";
	$q.= "WHERE pr.PackageID = ". $pkgid . " ";
	$q.= "ORDER BY pr.RelName";
	$ttl = config_get_int('options', 'cache_pkginfo_ttl');
	return db_cache_result($q, 'relations:' . $pkgid, PDO::FETCH_NUM, $ttl);
}

/**
 * Get the HTML code to display a package dependency link annotation
 * (dependency type, architecture, ...)
 *
 * @param string $type The name of the dependency type
 * @param string $arch The package dependency architecture
 * @param string $desc An optdepends description
 *
 * @return string The HTML code of the label to display
 */
function pkg_deplink_annotation($type, $arch, $desc=false) {
	if ($type == 'depends' && !$arch) {
		return '';
	}

	$link = ' <em>(';

	if ($type == 'makedepends') {
		$link .= 'make';
	} elseif ($type == 'checkdepends') {
		$link .= 'check';
	} elseif ($type == 'optdepends') {
		$link .= 'optional';
	}

	if ($type != 'depends' && $arch) {
		$link .= ', ';
	}

	if ($arch) {
		$link .= htmlspecialchars($arch);
	}

	$link .= ')';
	if ($type == 'optdepends' && $desc) {
		$link .= ' &ndash; ' . htmlspecialchars($desc) . ' </em>';
	}
	$link .= '</em>';

	return $link;
}

/**
 * Get the HTML code to display a package provider link
 *
 * @param string $name The name of the provider
 * @param bool $official True if the package is in the official repositories
 *
 * @return string The HTML code of the link to display
 */
function pkg_provider_link($name, $official) {
	$link = '<a href="';
	if ($official) {
		$link .= 'https://www.archlinux.org/packages/?q=' .
			urlencode($name);
	} else {
		$link .= htmlspecialchars(get_pkg_uri($name), ENT_QUOTES);
	}
	$link .= '" title="' . __('View packages details for') . ' ';
	$link .= htmlspecialchars($name) . '">';
	$link .= htmlspecialchars($name) . '</a>';

	return $link;
}

/**
 * Get the HTML code to display a package dependency link
 *
 * @param string $name The name of the dependency
 * @param string $type The name of the dependency type
 * @param string $desc The (optional) description of the dependency
 * @param string $cond The package dependency condition string
 * @param string $arch The package dependency architecture
 * @param int $pkg_id The package of the package to display the dependency for
 *
 * @return string The HTML code of the label to display
 */
function pkg_depend_link($name, $type, $desc, $cond, $arch, $pkg_id) {
	/*
	 * TODO: We currently perform one SQL query per nonexistent package
	 * dependency. It would be much better if we could annotate dependency
	 * data with providers so that we already know whether a dependency is
	 * a "provision name" or a package from the official repositories at
	 * this point.
	 */
	$providers = pkg_providers($name);

	if (count($providers) == 0) {
		$link = '<span class="broken">';
		$link .= htmlspecialchars($name);
		$link .= '</span>';
		$link .= htmlspecialchars($cond) . ' ';
		$link .= pkg_deplink_annotation($type, $arch, $desc);
		return $link;
	}

	$link = htmlspecialchars($name);
	foreach ($providers as $provider) {
		if ($provider[1] == $name) {
			$is_official = ($provider[0] == 0);
			$name = $provider[1];
			$link = pkg_provider_link($name, $is_official);
			break;
		}
	}
	$link .= htmlspecialchars($cond) . ' ';

	foreach ($providers as $key => $provider) {
		if ($provider[1] == $name) {
			unset($providers[$key]);
		}
	}

	if (count($providers) > 0) {
		$link .= '<span class="virtual-dep">(';
		foreach ($providers as $provider) {
			$is_official = ($provider[0] == 0);
			$name = $provider[1];
			$link .= pkg_provider_link($name, $is_official) . ', ';
		}
		$link = substr($link, 0, -2);
		$link .= ')</span>';
	}

	$link .= pkg_deplink_annotation($type, $arch, $desc);

	return $link;
}

/**
 * Get the HTML code to display a package requirement link
 *
 * @param string $name The name of the requirement
 * @param string $depends The (literal) name of the dependency of $name
 * @param string $type The name of the dependency type
 * @param string $arch The package dependency architecture
 * @param string $pkgname The name of dependant package
 *
 * @return string The HTML code of the link to display
 */
function pkg_requiredby_link($name, $depends, $type, $arch, $pkgname) {
	$link = '<a href="';
	$link .= htmlspecialchars(get_pkg_uri($name), ENT_QUOTES);
	$link .= '" title="' . __('View packages details for') .' ' . htmlspecialchars($name) . '">';
	$link .= htmlspecialchars($name) . '</a>';

	if ($depends != $pkgname) {
		$link .= ' <span class="virtual-dep">(';
		$link .= __('requires %s', htmlspecialchars($depends));
		$link .= ')</span>';
	}

	return $link . pkg_deplink_annotation($type, $arch);
}

/**
 * Get the HTML code to display a package relation
 *
 * @param string $name The name of the relation
 * @param string $cond The package relation condition string
 * @param string $arch The package relation architecture
 *
 * @return string The HTML code of the label to display
 */
function pkg_rel_html($name, $cond, $arch) {
	$html = htmlspecialchars($name) . htmlspecialchars($cond);

	if ($arch) {
		$html .= ' <em>(' . htmlspecialchars($arch) . ')</em>';
	}

	return $html;
}

/**
 * Get the HTML code to display a source link
 *
 * @param string $url The URL of the source
 * @param string $arch The source architecture
 * @param string $package The name of the package
 *
 * @return string The HTML code of the label to display
 */
function pkg_source_link($url, $arch, $package) {
	$url = explode('::', $url);
	$parsed_url = parse_url($url[0]);

	if (isset($parsed_url['scheme']) || isset($url[1])) {
		$link = '<a href="' .  htmlspecialchars((isset($url[1]) ? $url[1] : $url[0]), ENT_QUOTES) . '">' . htmlspecialchars($url[0]) . '</a>';
	} else {
		$file_url = sprintf(config_get('options', 'source_file_uri'), htmlspecialchars($url[0]), $package);
		$link = '<a href="' . $file_url . '">' . htmlspecialchars($url[0]) . '</a>';
	}

	if ($arch) {
		$link .= ' <em>(' . htmlspecialchars($arch) . ')</em>';
	}

	return $link;
}

/**
 * Determine packages that depend on a package
 *
 * @param string $name The package name for the dependency search
 * @param array $provides A list of virtual provisions of the package
 * @param int $limit An upper bound for the number of packages to retrieve
 *
 * @return array All packages that depend on the specified package name
 */
function pkg_required($name="", $provides, $limit) {
	$deps = array();
	if ($name != "") {
		$dbh = DB::connect();

		$name_list = $dbh->quote($name);
		foreach ($provides as $p) {
			$name_list .= ',' . $dbh->quote($p[0]);
		}

		$q = "SELECT p.Name, pd.DepName, dt.Name, pd.DepArch ";
		$q.= "FROM PackageDepends pd ";
		$q.= "LEFT JOIN Packages p ON p.ID = pd.PackageID ";
		$q.= "LEFT JOIN DependencyTypes dt ON dt.ID = pd.DepTypeID ";
		$q.= "WHERE pd.DepName IN (" . $name_list . ") ";
		$q.= "ORDER BY p.Name LIMIT " . intval($limit);
		/* Not invalidated by package updates. */
		return db_cache_result($q, 'required:' . $name, PDO::FETCH_NUM);
	}
	return $deps;
}

/**
 * Get all package sources for a specific package
 *
 * @param string $pkgid The package ID to get the sources for
 *
 * @return array All sources associated with a specific package
 */
function pkg_sources($pkgid) {
	$pkgid = intval($pkgid);
	if (!$pkgid) {
		return array();
	}
	$q = "SELECT Source, SourceArch FROM PackageSources ";
	$q.= "WHERE PackageID = " . $pkgid;
	$q.= " ORDER BY Source";
	$ttl = config_get_int('options', 'cache_pkginfo_ttl');
	return db_cache_result($q, 'required:' . $pkgid, PDO::FETCH_NUM, $ttl);
}

/**
 * Get the package details
 *
 * @param string $id The package ID to get description for
 *
 * @return array The package's details OR error message
 **/
function pkg_get_details($id=0) {
	$dbh = DB::connect();

	$q = "SELECT Packages.*, PackageBases.ID AS BaseID, ";
	$q.= "PackageBases.Name AS BaseName, PackageBases.NumVotes, ";
	$q.= "PackageBases.Popularity, PackageBases.OutOfDateTS, ";
	$q.= "PackageBases.SubmittedTS, PackageBases.ModifiedTS, ";
	$q.= "PackageBases.SubmitterUID, PackageBases.MaintainerUID, ";
	$q.= "PackageBases.PackagerUID, PackageBases.FlaggerUID, ";
	$q.= "(SELECT COUNT(*) FROM PackageRequests ";
	$q.= " WHERE PackageRequests.PackageBaseID = Packages.PackageBaseID ";
	$q.= " AND PackageRequests.Status = 0) AS RequestCount ";
	$q.= "FROM Packages, PackageBases ";
	$q.= "WHERE PackageBases.ID = Packages.PackageBaseID ";
	$q.= "AND Packages.ID = " . intval($id);
	$result = $dbh->query($q);

	$row = array();

	if (!$result) {
		$row['error'] = __("Error retrieving package details.");
	}
	else {
		$row = $result->fetch(PDO::FETCH_ASSOC);
		if (empty($row)) {
			$row['error'] = __("Package details could not be found.");
		}
	}

	return $row;
}

/**
 * Display the package details page
 *
 * @param string $id The package ID to get details page for
 * @param array $row Package details retrieved by pkg_get_details()
 * @param string $SID The session ID of the visitor
 *
 * @return void
 */
function pkg_display_details($id=0, $row, $SID="") {
	$dbh = DB::connect();

	if (isset($row['error'])) {
		print "<p>" . $row['error'] . "</p>\n";
	}
	else {
		$base_id = pkgbase_from_pkgid($id);
		$pkgbase_name = pkgbase_name_from_id($base_id);

		include('pkg_details.php');

		if ($SID) {
			include('pkg_comment_box.php');
		}

		$include_deleted = has_credential(CRED_COMMENT_VIEW_DELETED);

		$limit_pinned = isset($_GET['pinned']) ? 0 : 5;
		$pinned = pkgbase_comments($base_id, $limit_pinned, false, true);
		if (!empty($pinned)) {
			$comment_section = "package";
			include('pkg_comments.php');
		}
		unset($pinned);


		$total_comment_count = pkgbase_comments_count($base_id, $include_deleted);
		list($pagination_templs, $per_page, $offset) = calculate_pagination($total_comment_count);

		$comments = pkgbase_comments($base_id, $per_page, $include_deleted, false, $offset);
		if (!empty($comments)) {
			$comment_section = "package";
			include('pkg_comments.php');
		}
	}
}

/**
 * Output the body of the search results page
 *
 * @param array $params Search parameters
 * @param bool $show_headers True if statistics should be included
 * @param string $SID The session ID of the visitor
 *
 * @return int The total number of packages matching the query
 */
function pkg_search_page($params, $show_headers=true, $SID="") {
	$dbh = DB::connect();

	/*
	 * Get commonly used variables.
	 * TODO: Reduce the number of database queries!
	 */
	if ($SID)
		$myuid = uid_from_sid($SID);

	/* Sanitize paging variables. */
	if (isset($params['O'])) {
		$params['O'] = max(intval($params['O']), 0);
	} else {
		$params['O'] = 0;
	}

	if (isset($params["PP"])) {
		$params["PP"] = bound(intval($params["PP"]), 50, 250);
	} else {
		$params["PP"] = 50;
	}

	/*
	 * FIXME: Pull out DB-related code. All of it! This one's worth a
	 * choco-chip cookie, one of those nice big soft ones.
	 */

	/* Build the package search query. */
	$q_select = "SELECT ";
	if ($SID) {
		$q_select .= "PackageNotifications.UserID AS Notify,
			   PackageVotes.UsersID AS Voted, ";
	}
	$q_select .= "Users.Username AS Maintainer,
	Packages.Name, Packages.Version, Packages.Description,
	PackageBases.NumVotes, PackageBases.Popularity, Packages.ID,
	Packages.PackageBaseID, PackageBases.OutOfDateTS ";

	$q_from = "FROM Packages
	LEFT JOIN PackageBases ON (PackageBases.ID = Packages.PackageBaseID)
	LEFT JOIN Users ON (PackageBases.MaintainerUID = Users.ID) ";
	if ($SID) {
		/* This is not needed for the total row count query. */
		$q_from_extra = "LEFT JOIN PackageVotes
		ON (PackageBases.ID = PackageVotes.PackageBaseID AND PackageVotes.UsersID = $myuid)
		LEFT JOIN PackageNotifications
		ON (PackageBases.ID = PackageNotifications.PackageBaseID AND PackageNotifications.UserID = $myuid) ";
	} else {
		$q_from_extra = "";
	}

	$q_where = 'WHERE PackageBases.PackagerUID IS NOT NULL ';

	if (isset($params['K'])) {
		if (isset($params["SeB"]) && $params["SeB"] == "m") {
			/* Search by maintainer. */
			$q_where .= "AND Users.Username = " . $dbh->quote($params['K']) . " ";
		}
		elseif (isset($params["SeB"]) && $params["SeB"] == "c") {
			/* Search by co-maintainer. */
			$q_where .= "AND EXISTS (SELECT * FROM PackageComaintainers ";
			$q_where .= "INNER JOIN Users ON Users.ID = PackageComaintainers.UsersID ";
			$q_where .= "WHERE PackageComaintainers.PackageBaseID = PackageBases.ID ";
			$q_where .= "AND Users.Username = " . $dbh->quote($params['K']) . ")";
		}
		elseif (isset($params["SeB"]) && $params["SeB"] == "M") {
			/* Search by maintainer and co-maintainer. */
			$q_where .= "AND (Users.Username = " . $dbh->quote($params['K']) . " ";
			$q_where .= "OR EXISTS (SELECT * FROM PackageComaintainers ";
			$q_where .= "INNER JOIN Users ON Users.ID = PackageComaintainers.UsersID ";
			$q_where .= "WHERE PackageComaintainers.PackageBaseID = PackageBases.ID ";
			$q_where .= "AND Users.Username = " . $dbh->quote($params['K']) . "))";
		}
		elseif (isset($params["SeB"]) && $params["SeB"] == "s") {
			/* Search by submitter. */
			$q_where .= "AND SubmitterUID = " . intval(uid_from_username($params['K'])) . " ";
		}
		elseif (isset($params["SeB"]) && $params["SeB"] == "n") {
			/* Search by name. */
			$K = "%" . addcslashes($params['K'], '%_') . "%";
			$q_where .= "AND (Packages.Name LIKE " . $dbh->quote($K) . ") ";
		}
		elseif (isset($params["SeB"]) && $params["SeB"] == "b") {
			/* Search by package base name. */
			$K = "%" . addcslashes($params['K'], '%_') . "%";
			$q_where .= "AND (PackageBases.Name LIKE " . $dbh->quote($K) . ") ";
		}
		elseif (isset($params["SeB"]) && $params["SeB"] == "k") {
			/* Search by name. */
			$q_where .= "AND (";
			$q_where .= construct_keyword_search($dbh, $params['K'], false, true);
			$q_where .= ") ";
		}
		elseif (isset($params["SeB"]) && $params["SeB"] == "N") {
			/* Search by name (exact match). */
			$q_where .= "AND (Packages.Name = " . $dbh->quote($params['K']) . ") ";
		}
		elseif (isset($params["SeB"]) && $params["SeB"] == "B") {
			/* Search by package base name (exact match). */
			$q_where .= "AND (PackageBases.Name = " . $dbh->quote($params['K']) . ") ";
		}
		else {
			/* Keyword search (default). */
			$q_where .= "AND (";
			$q_where .= construct_keyword_search($dbh, $params['K'], true, true);
			$q_where .= ") ";
		}
	}

	if (isset($params["do_Orphans"])) {
		$q_where .= "AND MaintainerUID IS NULL ";
	}

	if (isset($params['outdated'])) {
		if ($params['outdated'] == 'on') {
			$q_where .= "AND OutOfDateTS IS NOT NULL ";
		}
		elseif ($params['outdated'] == 'off') {
			$q_where .= "AND OutOfDateTS IS NULL ";
		}
	}

	$order = (isset($params["SO"]) && $params["SO"] == 'd') ? 'DESC' : 'ASC';

	$q_sort = "ORDER BY ";
	$sort_by = isset($params["SB"]) ? $params["SB"] : '';
	switch ($sort_by) {
	case 'v':
		$q_sort .= "NumVotes " . $order . ", ";
		break;
	case 'p':
		$q_sort .= "Popularity " . $order . ", ";
		break;
	case 'w':
		if ($SID) {
			$q_sort .= "Voted " . $order . ", ";
		}
		break;
	case 'o':
		if ($SID) {
			$q_sort .= "Notify " . $order . ", ";
		}
		break;
	case 'm':
		$q_sort .= "Maintainer " . $order . ", ";
		break;
	case 'l':
		$q_sort .= "ModifiedTS " . $order . ", ";
		break;
	case 'a':
		/* For compatibility with old search links. */
		$q_sort .= "-ModifiedTS " . $order . ", ";
		break;
	default:
		break;
	}
	$q_sort .= " Packages.Name " . $order . " ";

	$q_limit = "LIMIT ".$params["PP"]." OFFSET ".$params["O"];

	$q = $q_select . $q_from . $q_from_extra . $q_where . $q_sort . $q_limit;
	$q_total = "SELECT COUNT(*) " . $q_from . $q_where;

	$result = $dbh->query($q);
	$result_t = $dbh->query($q_total);
	if ($result_t) {
		$row = $result_t->fetch(PDO::FETCH_NUM);
		$total = $row[0];
	}
	else {
		$total = 0;
	}

	if ($result && $total > 0) {
		if (isset($params["SO"]) && $params["SO"] == "d"){
			$SO_next = "a";
		}
		else {
			$SO_next = "d";
		}
	}

	/* Calculate the results to use. */
	$first = $params['O'] + 1;

	/* Calculation of pagination links. */
	$per_page = ($params['PP'] > 0) ? $params['PP'] : 50;
	$current = ceil($first / $per_page);
	$pages = ceil($total / $per_page);
	$templ_pages = array();

	if ($current > 1) {
		$templ_pages['&laquo; ' . __('First')] = 0;
		$templ_pages['&lsaquo; ' . __('Previous')] = ($current - 2) * $per_page;
	}

	if ($current - 5 > 1)
		$templ_pages["..."] = false;

	for ($i = max($current - 5, 1); $i <= min($pages, $current + 5); $i++) {
		$templ_pages[$i] = ($i - 1) * $per_page;
	}

	if ($current + 5 < $pages)
		$templ_pages["... "] = false;

	if ($current < $pages) {
		$templ_pages[__('Next') . ' &rsaquo;'] = $current * $per_page;
		$templ_pages[__('Last') . ' &raquo;'] = ($pages - 1) * $per_page;
	}

	$searchresults = array();
	if ($result) {
		while ($row = $result->fetch(PDO::FETCH_ASSOC)) {
			$searchresults[] = $row;
		}
	}

	include('pkg_search_results.php');

	return $total;
}

/**
 * Construct the WHERE part of the sophisticated keyword search
 *
 * @param handle $dbh Database handle
 * @param string $keywords The search term
 * @param bool $namedesc Search name and description fields
 * @param bool $keyword Search packages with a matching PackageBases.Keyword
 *
 * @return string WHERE part of the SQL clause
 */
function construct_keyword_search($dbh, $keywords, $namedesc, $keyword=false) {
	$count = 0;
	$where_part = "";
	$q_keywords = "";
	$op = "";

	foreach (str_getcsv($keywords, ' ') as $term) {
		if ($term == "") {
			continue;
		}
		if ($count > 0 && strtolower($term) == "and") {
			$op = "AND ";
			continue;
		}
		if ($count > 0 && strtolower($term) == "or") {
			$op = "OR ";
			continue;
		}
	        if ($count > 0 && strtolower($term) == "not") {
			$op .= "NOT ";
			continue;
		}

		$term = "%" . addcslashes($term, '%_') . "%";
		$q_keywords .= $op . " (";
		$q_keywords .= "Packages.Name LIKE " . $dbh->quote($term) . " ";
		if ($namedesc) {
			$q_keywords .= "OR Description LIKE " . $dbh->quote($term) . " ";
		}

		if ($keyword) {
			$q_keywords .= "OR EXISTS (SELECT * FROM PackageKeywords WHERE ";
			$q_keywords .= "PackageKeywords.PackageBaseID = Packages.PackageBaseID AND ";
			$q_keywords .= "PackageKeywords.Keyword LIKE " . $dbh->quote($term) . ")) ";
		} else {
			$q_keywords .= ") ";
		}

		$count++;
		if ($count >= 20) {
			break;
		}
		$op = "AND ";
	}

	return $q_keywords;
}

/**
 * Determine if a POST string has been sent by a visitor
 *
 * @param string $action String to check has been sent via POST
 *
 * @return bool True if the POST string was used, otherwise false
 */
function current_action($action) {
	return (isset($_POST['action']) && $_POST['action'] == $action) ||
		isset($_POST[$action]);
}

/**
 * Determine if sent IDs are valid integers
 *
 * @param array $ids IDs to validate
 *
 * @return array All sent IDs that are valid integers
 */
function sanitize_ids($ids) {
	$new_ids = array();
	foreach ($ids as $id) {
		$id = intval($id);
		if ($id > 0) {
			$new_ids[] = $id;
		}
	}
	return $new_ids;
}

/**
 * Determine package information for latest package
 *
 * @param int $numpkgs Number of packages to get information on
 *
 * @return array $packages Package info for the specified number of recent packages
 */
function latest_pkgs($numpkgs) {
	$dbh = DB::connect();

	$q = "SELECT Packages.*, MaintainerUID, SubmittedTS ";
	$q.= "FROM Packages LEFT JOIN PackageBases ON ";
	$q.= "PackageBases.ID = Packages.PackageBaseID ";
	$q.= "ORDER BY SubmittedTS DESC ";
	$q.= "LIMIT " . intval($numpkgs);
	$result = $dbh->query($q);

	$packages = array();
	if ($result) {
		while ($row = $result->fetch(PDO::FETCH_ASSOC)) {
			$packages[] = $row;
		}
	}

	return $packages;
}
