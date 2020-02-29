T = $(sort $(wildcard *.t))

PROVE := $(shell command -v prove 2> /dev/null)

ifdef PROVE
check:
	prove .
else
check: $(T)
endif

clean:
	$(RM) -r test-results/

$(T):
	@echo "*** $@ ***"; $(SHELL) $@

.PHONY: check $(FOREIGN_TARGETS) clean $(T)
