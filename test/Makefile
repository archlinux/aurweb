T = $(sort $(wildcard *.t))

PROVE := $(shell command -v prove 2> /dev/null)

MAKEFLAGS = -j1

# IMPORTANT: `sh` should come somewhere AFTER `pytest`.
check: sh pytest

pytest:
	cd .. && AUR_CONFIG=conf/config coverage run --append /usr/bin/pytest test

ifdef PROVE
sh:
	prove .
else
sh: $(T)
endif

clean:
	$(RM) -r test-results/

$(T):
	@echo "*** $@ ***"; $(SHELL) $@

.PHONY: check $(FOREIGN_TARGETS) clean $(T)
