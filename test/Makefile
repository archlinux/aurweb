T = $(sort $(wildcard *.t))

PROVE := $(shell command -v prove 2> /dev/null)

MAKEFLAGS = -j1

# IMPORTANT: `sh` should come somewhere AFTER `pytest`.
check: sh pytest

pytest:
	cd .. && coverage run --append /usr/bin/pytest test

ifdef PROVE
sh:
	prove .
else
sh: $(T)
endif

coverage:
	cd .. && coverage report --include='aurweb/*'
	cd .. && coverage xml --include='aurweb/*'

clean:
	$(RM) -r test-results/
	rm -f ../.coverage

$(T):
	@echo "*** $@ ***"; $(SHELL) $@

.PHONY: check coverage $(FOREIGN_TARGETS) clean $(T)
