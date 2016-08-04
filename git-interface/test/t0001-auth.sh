#!/bin/sh

test_description='git-auth tests'

. ./setup.sh

test_expect_success 'Test basic authentication.' '
	"$GIT_AUTH" "$AUTH_KEYTYPE_USER" "$AUTH_KEYTEXT_USER" >out &&
	grep -q AUR_USER=user out &&
	grep -q AUR_PRIVILEGED=0 out
'

test_expect_success 'Test Trusted User authentication.' '
	"$GIT_AUTH" "$AUTH_KEYTYPE_TU" "$AUTH_KEYTEXT_TU" >out &&
	grep -q AUR_USER=tu out &&
	grep -q AUR_PRIVILEGED=1 out
'

test_done
