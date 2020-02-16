T = $(sort $(wildcard t[0-9][0-9][0-9][0-9]-*.sh))

check: $(T)

clean:
	$(RM) -r test-results/

$(T):
	@echo "*** $@ ***"; $(SHELL) $@

.PHONY: check $(FOREIGN_TARGETS) clean $(T)
