GIT_INTERFACE_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))

include config.mk

git-auth.sh:
	sed 's#%GIT_INTERFACE_DIR%#$(GIT_INTERFACE_DIR)#' <git-auth.sh.in >git-auth.sh
	chmod +x git-auth.sh

install: git-auth.sh
	install -Dm0755 git-auth.sh "$(DESTDIR)$(PREFIX)/bin/aur-git-auth"

uninstall:
	rm -f "$(DESTDIR)$(PREFIX)/bin/aur-git-auth"

clean:
	rm -f git-auth.sh

.PHONY: install uninstall clean
