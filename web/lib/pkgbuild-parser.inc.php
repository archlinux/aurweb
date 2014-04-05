# <?php
if (!$error) {
	# process PKGBUILD - remove line concatenation
	#
	$pkgbuild = array();
	$line_no = 0;
	$lines = array();
	$continuation_line = 0;
	$current_line = "";
	$paren_depth = 0;
	foreach (explode("\n", $pkgbuild_raw) as $line) {
		$line = trim($line);
		# Remove comments
		$line = preg_replace('/\s*#.*/', '', $line);

		$char_counts = count_chars($line, 0);
		$paren_depth += $char_counts[ord('(')] - $char_counts[ord(')')];
		if (substr($line, strlen($line)-1) == "\\") {
			# continue appending onto existing line_no
			#
			$current_line .= substr($line, 0, strlen($line)-1);
			$continuation_line = 1;
		} elseif ($paren_depth > 0) {
			# assumed continuation
			# continue appending onto existing line_no
			#
			$current_line .= $line . " ";
			$continuation_line = 1;
		} else {
			# maybe the last line in a continuation, or a standalone line?
			#
			if ($continuation_line) {
				# append onto existing line_no
				#
				$current_line .= $line;
				$lines[$line_no] = $current_line;
				$current_line = "";
			} else {
				# it's own line_no
				#
				$lines[$line_no] = $line;
			}
			$continuation_line = 0;
			$line_no++;
		}
	}

	# Now process the lines and put any var=val lines into the
	# 'pkgbuild' array.
	while (list($k, $line) = each($lines)) {
		# Neutralize parameter substitution
		$line = preg_replace('/\${(\w+)#(\w*)}?/', '$1$2', $line);

		$lparts = Array();
		# Match variable assignment only.
		if (preg_match('/^\s*[_\w]+=[^=].*/', $line, $matches)) {
			$lparts = explode("=", $matches[0], 2);
		}

		if (!empty($lparts)) {
			# this is a variable/value pair, strip
			# out array parens and any quoting,
			# except in pkgdesc for pkgname or
			# pkgdesc, only remove start/end pairs
			# of " or '
			if ($lparts[0] == "pkgname" || $lparts[0] == "pkgdesc") {
				if ($lparts[1]{0} == '"' &&
						$lparts[1]{strlen($lparts[1])-1} == '"') {
					$pkgbuild[$lparts[0]] = substr($lparts[1], 1, -1);
				}
				elseif
					($lparts[1]{0} == "'" &&
					 $lparts[1]{strlen($lparts[1])-1} == "'") {
					$pkgbuild[$lparts[0]] = substr($lparts[1], 1, -1);
				} else {
					$pkgbuild[$lparts[0]] = $lparts[1];
				}
			} else {
				$pkgbuild[$lparts[0]] = str_replace(array("(",")","\"","'"), "",
						$lparts[1]);
			}
		}
	}

	# some error checking on PKGBUILD contents - just make sure each
	# variable has a value. This does not do any validity checking
	# on the values, or attempts to fix line continuation/wrapping.
	$req_vars = array("url", "pkgdesc", "license", "pkgrel", "pkgver", "arch", "pkgname");
	foreach ($req_vars as $var) {
		if (!array_key_exists($var, $pkgbuild)) {
			$error = __('Missing %s variable in PKGBUILD.', $var);
			break;
		}
	}
}

# Now, run through the pkgbuild array, and do "eval" and simple substituions.
$new_pkgbuild = array();
if (!$error) {
	while (list($k, $v) = each($pkgbuild)) {
		if (strpos($k,'eval ') !== false) {
			$k = preg_replace('/^eval[\s]*/', "", $k);
			##"eval" replacements
			$pattern_eval = '/{\$({?)([\w]+)(}?)}/';
			while (preg_match($pattern_eval,$v,$regs)) {
				$pieces = explode(",",$pkgbuild["$regs[2]"]);
				## nongreedy matching! - preserving the order of "eval"
				$pattern = '/([\S]*?){\$'.$regs[1].$regs[2].$regs[3].'}([\S]*)/';
				while (preg_match($pattern,$v,$regs_replace)) {
					$replacement = "";
					for ($i = 0; $i < sizeof($pieces); $i++) {
						$replacement .= $regs_replace[1].$pieces[$i].$regs_replace[2]." ";
					}
					$v=preg_replace($pattern, $replacement, $v, 1);
				}
			}
		}

		# Simple variable replacement
		$pattern_var = '/\$({?)([_\w]+)(}?)/';
		$offset = 0;
		while (preg_match($pattern_var, $v, $regs, PREG_OFFSET_CAPTURE, $offset)) {
			$var = $regs[2][0];
			$pos = $regs[0][1];
			$len = strlen($regs[0][0]);

			if (isset($new_pkgbuild[$var])) {
				$replacement = substr($new_pkgbuild[$var], strpos($new_pkgbuild[$var], " "));
			}
			else {
				$replacement = '';
			}

			$v = substr_replace($v, $replacement, $pos, $len);
			$offset = $pos + strlen($replacement);
		}
		$new_pkgbuild[$k] = $v;
	}
}
