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

test_expect_success 'Test authentication with an unsupported key type.' '
	test_must_fail "$GIT_AUTH" ssh-xxx "$AUTH_KEYTEXT_USER"
'

test_expect_success 'Test authentication with a wrong key.' '
	"$GIT_AUTH" "$AUTH_KEYTYPE_MISSING" "$AUTH_KEYTEXT_MISSING" >out
	test_must_be_empty out
'

test_expect_success 'Test AUR_OVERWRITE passthrough.' '
	AUR_OVERWRITE=1 \
	"$GIT_AUTH" "$AUTH_KEYTYPE_TU" "$AUTH_KEYTEXT_TU" >out &&
	grep -q AUR_OVERWRITE=1 out
'

test_expect_success 'Make sure that AUR_OVERWRITE is unset by default.' '
	"$GIT_AUTH" "$AUTH_KEYTYPE_TU" "$AUTH_KEYTEXT_TU" >out &&
	grep -q AUR_OVERWRITE=0 out
'

test_expect_success 'Make sure regular users cannot set AUR_OVERWRITE.' '
	AUR_OVERWRITE=1 \
	"$GIT_AUTH" "$AUTH_KEYTYPE_USER" "$AUTH_KEYTEXT_USER" >out &&
	grep -q AUR_OVERWRITE=0 out
'

test_done
