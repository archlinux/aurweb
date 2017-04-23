#!/bin/sh

test_description='rendercomment tests'

. ./setup.sh

test_expect_success 'Test comment rendering.' '
	cat <<-EOD | sqlite3 aur.db &&
	INSERT INTO PackageComments (ID, PackageBaseID, Comments, RenderedComment) VALUES (1, 1, "Hello world!
	This is a comment.", "");
	EOD
	"$RENDERCOMMENT" 1 &&
	cat <<-EOD >expected &&
	<p>Hello world!<br>
	This is a comment.</p>
	EOD
	cat <<-EOD | sqlite3 aur.db >actual &&
	SELECT RenderedComment FROM PackageComments WHERE ID = 1;
	EOD
	test_cmp actual expected
'

test_done
