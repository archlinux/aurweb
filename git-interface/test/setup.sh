TEST_DIRECTORY="$(pwd)"

. ./sharness.sh

# Configure paths to the Git interface scripts.
GIT_AUTH="$TEST_DIRECTORY/../git-auth.py"
GIT_SERVE="$TEST_DIRECTORY/../git-serve.py"
GIT_UPDATE="$TEST_DIRECTORY/../git-update.py"

# Create the configuration file and a dummy notification script.
cat >config <<-EOF
[database]
backend = sqlite
name = aur.db

[options]
enable-maintenance = 0
maintenance-exceptions = 127.0.0.1

[notifications]
notify-cmd = ./notify.sh

[auth]
valid-keytypes = ssh-rsa ssh-dss ecdsa-sha2-nistp256 ecdsa-sha2-nistp384 ecdsa-sha2-nistp521 ssh-ed25519
username-regex = [a-zA-Z0-9]+[.\-_]?[a-zA-Z0-9]+$
git-serve-cmd = /srv/http/aurweb/git-interface/git-serve.py
ssh-options = restrict

[serve]
repo-path = ./aur.git/
repo-regex = [a-z0-9][a-z0-9.+_-]*$
git-shell-cmd = /usr/bin/git-shell
git-update-cmd = /srv/http/aurweb/git-interface/git-update.py
ssh-cmdline = ssh aur@aur.archlinux.org

[update]
max-blob-size = 256000
EOF

cat >notify.sh <<-EOF
#!/bin/sh
EOF
chmod +x notify.sh

AUR_CONFIG=config
export AUR_CONFIG

# Create SSH public keys which will be used by the test users later.
AUTH_KEYTYPE_USER=ssh-rsa
AUTH_KEYTEXT_USER=AAAAB3NzaC1yc2EAAAADAQABAAABAQCeUafDK4jqUiRHNQfwHcYjBKLZ4Rc1sNUofHApBP6j91nIvDHZe2VUqeBmFUhBz7kXK4VbXD9nlHMun2HeshL8hXnMzymZ8Wk7+IKefj61pajJkIdttw9Tnayfg7uhg5RbFy9zpEjmGjnIVjSzOXKCwppNT+CNujpKM5FD8gso/Z+l3fD+IwrPwS1SzF1Z99nqI9n2FM/JWZqluvTqnW9WdAvBDfutXxp0R5ZiLI5TAKL2Ssp5rpL70pkLXhv+9sK545zKKlXUFmw6Pi2iVBdqdRsk9ocl49dLiNIh8CYDCO3CRQn+8EnpBhTor2TKQxGJI3mzoBwWJJxoKhD/XlYJ
AUTH_FINGERPRINT_USER=SHA256:F/OFtYAy0JCytAGUi4RUZnOsThhQtFMK7fH1YvFBCpo

AUTH_KEYTYPE_TU=ssh-rsa
AUTH_KEYTEXT_TU=AAAAB3NzaC1yc2EAAAADAQABAAABAQC4Q2Beg6jf2r1LZ4vwT5y10dK8+/c5RaNyTwv77wF2OSLXh32xW0ovhE2lW2gqoakdGsxgM2fTtqMTl29WOsAxlGF7x9XbWhFXFUT88Daq1fAeuihkiRjfBbInSW/WcrFZ+biLBch67addtfkkd4PmAafDeeCtszAXqza+ltBG1oxAGiTXgI3LOhA1/GtLLxsi5sPUO3ZlhvwDn4Sy0aXYx8l9hop/PU4Cjn82hyRa9r+SRxQ3KtjKxcVMnZ8IyXOrBwXTukgSBR/6nSdEmO0JPkYUFuNwh3UGFKuNkrPguL5T+4YDym6czYmZJzQ7NNl2pLKYmYgBwBe5rORlWfN5
AUTH_FINGERPRINT_TU=SHA256:xQGC6j/U1Q3NDXLl04pm+Shr1mjYUXbGMUzlm9vby4k

# Initialize the test database.
rm -f aur.db
sed \
	-e '/^DROP DATABASE /d' \
	-e '/^CREATE DATABASE /d' \
	-e '/^USE /d' \
	-e 's/ ENGINE = InnoDB//' \
	-e 's/ [A-Z]* UNSIGNED NOT NULL AUTO_INCREMENT/ INTEGER NOT NULL/' \
	-e 's/([0-9, ]*) UNSIGNED / UNSIGNED /' \
	"$TEST_DIRECTORY/../../schema/aur-schema.sql" | sqlite3 aur.db

echo "INSERT INTO Users (ID, UserName, Passwd, Email, AccountTypeID) VALUES (1, 'user', '!', 'user@localhost', 1);" | sqlite3 aur.db
echo "INSERT INTO Users (ID, UserName, Passwd, Email, AccountTypeID) VALUES (2, 'tu', '!', 'tu@localhost', 2);" | sqlite3 aur.db

echo "INSERT INTO SSHPubKeys (UserID, Fingerprint, PubKey) VALUES (1, '$AUTH_FINGERPRINT_USER', '$AUTH_KEYTYPE_USER $AUTH_KEYTEXT_USER');" | sqlite3 aur.db
echo "INSERT INTO SSHPubKeys (UserID, Fingerprint, PubKey) VALUES (2, '$AUTH_FINGERPRINT_TU', '$AUTH_KEYTYPE_TU $AUTH_KEYTEXT_TU');" | sqlite3 aur.db

# Initialize a Git repository to store test packages in.
(
	GIT_AUTHOR_EMAIL=author@example.com
	GIT_AUTHOR_NAME='A U Thor'
	GIT_COMMITTER_EMAIL=committer@example.com
	GIT_COMMITTER_NAME='C O Mitter'
	export GIT_AUTHOR_EMAIL GIT_AUTHOR_NAME
	export GIT_COMMITTER_EMAIL GIT_COMMITTER_NAME

	mkdir aur.git
	cd aur.git

	git init -q
	git checkout -q -b refs/namespaces/foobar/refs/heads/master

	cat >PKGBUILD <<-EOF
	pkgname=foobar
	pkgver=1
	pkgrel=1
	pkgdesc='aurweb test package.'
	url='https://aur.archlinux.org/'
	license=('GPL')
	arch=('any')
	depends=('python-pygit2')
	source=()
	md5sums=()

	package() {
		echo 'Hello world!'
	}
	EOF

	cat >.SRCINFO <<-EOF
	pkgbase = foobar
		pkgdesc = aurweb test package.
		pkgver = 1
		pkgrel = 1
		url = https://aur.archlinux.org/
		arch = any
		license = GPL
		depends = python-pygit2

	pkgname = foobar
	EOF

	git add PKGBUILD .SRCINFO
	git commit -q -am 'Initial import'
)
