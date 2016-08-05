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
	SSH_ORIGINAL_COMMAND="setup-repo foobar2" AUR_USER=tu \
	"$GIT_SERVE" 2>&1 &&
	cat >expected <<-EOF &&
	*foobar
	EOF
	SSH_ORIGINAL_COMMAND="list-repos" AUR_USER=user \
	"$GIT_SERVE" 2>&1 >actual &&
	test_cmp expected actual
'

test_expect_success 'Test git-receive-pack.' '
	cat >expected <<-EOF &&
	user
	foobar
	foobar
	EOF
	SSH_ORIGINAL_COMMAND="git-receive-pack /foobar.git/" \
	AUR_USER=user AUR_PRIVILEGED=0 \
	"$GIT_SERVE" 2>&1 >actual &&
	test_cmp expected actual
'

test_expect_success 'Test git-receive-pack with an invalid repository name.' '
	SSH_ORIGINAL_COMMAND="git-receive-pack /!.git/" \
	AUR_USER=user AUR_PRIVILEGED=0 \
	test_must_fail "$GIT_SERVE" 2>&1 >actual
'

test_expect_success "Test git-upload-pack." '
	cat >expected <<-EOF &&
	user
	foobar
	foobar
	EOF
	SSH_ORIGINAL_COMMAND="git-upload-pack /foobar.git/" \
	AUR_USER=user AUR_PRIVILEGED=0 \
	"$GIT_SERVE" 2>&1 >actual &&
	test_cmp expected actual
'

test_expect_success "Try to pull from someone else's repository." '
	cat >expected <<-EOF &&
	user
	foobar2
	foobar2
	EOF
	SSH_ORIGINAL_COMMAND="git-upload-pack /foobar2.git/" \
	AUR_USER=user AUR_PRIVILEGED=0 \
	"$GIT_SERVE" 2>&1 >actual &&
	test_cmp expected actual
'

test_expect_success "Try to push to someone else's repository." '
	SSH_ORIGINAL_COMMAND="git-receive-pack /foobar2.git/" \
	AUR_USER=user AUR_PRIVILEGED=0 \
	test_must_fail "$GIT_SERVE" 2>&1
'

test_expect_success "Try to push to someone else's repository as Trusted User." '
	cat >expected <<-EOF &&
	tu
	foobar
	foobar
	EOF
	SSH_ORIGINAL_COMMAND="git-receive-pack /foobar.git/" \
	AUR_USER=tu AUR_PRIVILEGED=1 \
	"$GIT_SERVE" 2>&1 >actual &&
	test_cmp expected actual
'

test_expect_success "Test restore." '
	echo "DELETE FROM PackageBases WHERE Name = \"foobar\";" | \
	sqlite3 aur.db &&
	cat >expected <<-EOF &&
	user
	foobar
	EOF
	SSH_ORIGINAL_COMMAND="restore foobar" AUR_USER=user AUR_PRIVILEGED=0 \
	"$GIT_SERVE" 2>&1 >actual
	test_cmp expected actual
'

test_expect_success "Try to restore an existing package base." '
	SSH_ORIGINAL_COMMAND="restore foobar2" AUR_USER=user AUR_PRIVILEGED=0 \
	test_must_fail "$GIT_SERVE" 2>&1
'

test_done
