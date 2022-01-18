#!/bin/sh

test_description='git-auth tests'

. "$(dirname "$0")/setup.sh"


test_expect_success 'Test basic authentication.' '
	cover "$GIT_AUTH" "$AUTH_KEYTYPE_USER" "$AUTH_KEYTEXT_USER" >out &&
	grep -q AUR_USER=user out &&
	grep -q AUR_PRIVILEGED=0 out
'

test_expect_success 'Test Trusted User authentication.' '
	cover "$GIT_AUTH" "$AUTH_KEYTYPE_TU" "$AUTH_KEYTEXT_TU" >out &&
	grep -q AUR_USER=tu out &&
	grep -q AUR_PRIVILEGED=1 out
'

test_expect_success 'Test authentication with an unsupported key type.' '
	test_must_fail cover "$GIT_AUTH" ssh-xxx "$AUTH_KEYTEXT_USER"
'

test_expect_success 'Test authentication with a wrong key.' '
	cover "$GIT_AUTH" "$AUTH_KEYTYPE_MISSING" "$AUTH_KEYTEXT_MISSING" >out
	test_must_be_empty out
'

test_done
