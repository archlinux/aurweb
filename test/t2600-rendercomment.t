#!/bin/sh

test_description='rendercomment tests'

. "$(dirname "$0")/setup.sh"

test_expect_success 'Test comment rendering.' '
	cat <<-EOD | sqlite3 aur.db &&
	INSERT INTO PackageBases (ID, Name, PackagerUID, SubmittedTS, ModifiedTS, FlaggerComment) VALUES (1, "foobar", 1, 0, 0, "");
	INSERT INTO PackageComments (ID, PackageBaseID, Comments, RenderedComment) VALUES (1, 1, "Hello world!
	This is a comment.", "");
	EOD
	cover "$RENDERCOMMENT" 1 &&
	cat <<-EOD >expected &&
	<p>Hello world!
	This is a comment.</p>
	EOD
	cat <<-EOD | sqlite3 aur.db >actual &&
	SELECT RenderedComment FROM PackageComments WHERE ID = 1;
	EOD
	test_cmp actual expected
'

test_expect_success 'Test Markdown conversion.' '
	cat <<-EOD | sqlite3 aur.db &&
	INSERT INTO PackageComments (ID, PackageBaseID, Comments, RenderedComment) VALUES (2, 1, "*Hello* [world](https://www.archlinux.org/)!", "");
	EOD
	cover "$RENDERCOMMENT" 2 &&
	cat <<-EOD >expected &&
	<p><em>Hello</em> <a href="https://www.archlinux.org/">world</a>!</p>
	EOD
	cat <<-EOD | sqlite3 aur.db >actual &&
	SELECT RenderedComment FROM PackageComments WHERE ID = 2;
	EOD
	test_cmp actual expected
'

test_expect_success 'Test HTML sanitizing.' '
	cat <<-EOD | sqlite3 aur.db &&
	INSERT INTO PackageComments (ID, PackageBaseID, Comments, RenderedComment) VALUES (3, 1, "<script>alert(""XSS!"");</script>", "");
	EOD
	cover "$RENDERCOMMENT" 3 &&
	cat <<-EOD >expected &&
	&lt;script&gt;alert("XSS!");&lt;/script&gt;
	EOD
	cat <<-EOD | sqlite3 aur.db >actual &&
	SELECT RenderedComment FROM PackageComments WHERE ID = 3;
	EOD
	test_cmp actual expected
'

test_expect_success 'Test link conversion.' '
	cat <<-EOD | sqlite3 aur.db &&
	INSERT INTO PackageComments (ID, PackageBaseID, Comments, RenderedComment) VALUES (4, 1, "
		Visit https://www.archlinux.org/#_test_.
		Visit *https://www.archlinux.org/*.
		Visit <https://www.archlinux.org/>.
		Visit \`https://www.archlinux.org/\`.
		Visit [Arch Linux](https://www.archlinux.org/).
		Visit [Arch Linux][arch].
		[arch]: https://www.archlinux.org/
	", "");
	EOD
	cover "$RENDERCOMMENT" 4 &&
	cat <<-EOD >expected &&
		<p>Visit <a href="https://www.archlinux.org/#_test_">https://www.archlinux.org/#_test_</a>.
		Visit <em><a href="https://www.archlinux.org/">https://www.archlinux.org/</a></em>.
		Visit <a href="https://www.archlinux.org/">https://www.archlinux.org/</a>.
		Visit <code>https://www.archlinux.org/</code>.
		Visit <a href="https://www.archlinux.org/">Arch Linux</a>.
		Visit <a href="https://www.archlinux.org/">Arch Linux</a>.</p>
	EOD
	cat <<-EOD | sqlite3 aur.db >actual &&
	SELECT RenderedComment FROM PackageComments WHERE ID = 4;
	EOD
	test_cmp actual expected
'

test_expect_success 'Test Git commit linkification.' '
	local oid=`git -C aur.git rev-parse --verify HEAD`
	cat <<-EOD | sqlite3 aur.db &&
	INSERT INTO PackageComments (ID, PackageBaseID, Comments, RenderedComment) VALUES (5, 1, "
		$oid
		${oid:0:7}
		x.$oid.x
		${oid}x
		0123456789abcdef
		\`$oid\`
		http://example.com/$oid
	", "");
	EOD
	cover "$RENDERCOMMENT" 5 &&
	cat <<-EOD >expected &&
		<p><a href="https://aur.archlinux.org/cgit/aur.git/log/?h=foobar&amp;id=${oid:0:12}">${oid:0:12}</a>
		<a href="https://aur.archlinux.org/cgit/aur.git/log/?h=foobar&amp;id=${oid:0:7}">${oid:0:7}</a>
		x.<a href="https://aur.archlinux.org/cgit/aur.git/log/?h=foobar&amp;id=${oid:0:12}">${oid:0:12}</a>.x
		${oid}x
		0123456789abcdef
		<code>$oid</code>
		<a href="http://example.com/$oid">http://example.com/$oid</a></p>
	EOD
	cat <<-EOD | sqlite3 aur.db >actual &&
	SELECT RenderedComment FROM PackageComments WHERE ID = 5;
	EOD
	test_cmp actual expected
'

test_expect_success 'Test Flyspray issue linkification.' '
	sqlite3 aur.db <<-EOD &&
	INSERT INTO PackageComments (ID, PackageBaseID, Comments, RenderedComment) VALUES (6, 1, "
		FS#1234567.
		*FS#1234*
		FS#
		XFS#1
		\`FS#1234\`
		https://archlinux.org/?test=FS#1234
	", "");
	EOD
	cover "$RENDERCOMMENT" 6 &&
	cat <<-EOD >expected &&
		<p><a href="https://bugs.archlinux.org/task/1234567">FS#1234567</a>.
		<em><a href="https://bugs.archlinux.org/task/1234">FS#1234</a></em>
		FS#
		XFS#1
		<code>FS#1234</code>
		<a href="https://archlinux.org/?test=FS#1234">https://archlinux.org/?test=FS#1234</a></p>
	EOD
	sqlite3 aur.db <<-EOD >actual &&
	SELECT RenderedComment FROM PackageComments WHERE ID = 6;
	EOD
	test_cmp actual expected
'

test_expect_success 'Test headings lowering.' '
	sqlite3 aur.db <<-EOD &&
	INSERT INTO PackageComments (ID, PackageBaseID, Comments, RenderedComment) VALUES (7, 1, "
		# One
		## Two
		### Three
		#### Four
		##### Five
		###### Six
	", "");
	EOD
	cover "$RENDERCOMMENT" 7 &&
	cat <<-EOD >expected &&
		<h5>One</h5>
		<h6>Two</h6>
		<h6>Three</h6>
		<h6>Four</h6>
		<h6>Five</h6>
		<h6>Six</h6>
	EOD
	sqlite3 aur.db <<-EOD >actual &&
	SELECT RenderedComment FROM PackageComments WHERE ID = 7;
	EOD
	test_cmp actual expected
'

test_done
