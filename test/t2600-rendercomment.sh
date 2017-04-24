#!/bin/sh

test_description='rendercomment tests'

. ./setup.sh

test_expect_success 'Test comment rendering.' '
	cat <<-EOD | sqlite3 aur.db &&
	INSERT INTO PackageBases (ID, Name, PackagerUID, SubmittedTS, ModifiedTS, FlaggerComment) VALUES (1, "foobar", 1, 0, 0, "");
	INSERT INTO PackageComments (ID, PackageBaseID, Comments, RenderedComment) VALUES (1, 1, "Hello world!
	This is a comment.", "");
	EOD
	"$RENDERCOMMENT" 1 &&
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
	"$RENDERCOMMENT" 2 &&
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
	"$RENDERCOMMENT" 3 &&
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
	INSERT INTO PackageComments (ID, PackageBaseID, Comments, RenderedComment) VALUES (4, 1, "Visit https://www.archlinux.org/.", "");
	EOD
	"$RENDERCOMMENT" 4 &&
	cat <<-EOD >expected &&
	<p>Visit <a href="https://www.archlinux.org/">https://www.archlinux.org/</a>.</p>
	EOD
	cat <<-EOD | sqlite3 aur.db >actual &&
	SELECT RenderedComment FROM PackageComments WHERE ID = 4;
	EOD
	test_cmp actual expected
'

test_done
