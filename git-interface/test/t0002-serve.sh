#!/bin/sh

test_description='git-serve tests'

. ./setup.sh

test_expect_success 'Test interactive shell.' '
	"$GIT_SERVE" 2>&1 | grep -q "Interactive shell is disabled."
'

test_expect_success 'Test help.' '
	SSH_ORIGINAL_COMMAND=help "$GIT_SERVE" 2>&1 | grep -q "^Commands:$"
'

test_expect_success 'Test setup-repo and list-repos.' '
	SSH_ORIGINAL_COMMAND="setup-repo foobar" AUR_USER=user \
	"$GIT_SERVE" 2>&1 &&
	cat >expected <<-EOF &&
	*foobar
	EOF
	SSH_ORIGINAL_COMMAND="list-repos" AUR_USER=user \
	"$GIT_SERVE" 2>&1 >actual &&
	test_cmp expected actual
'

test_done
