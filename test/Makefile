FOREIGN_TARGETS = ../schema/aur-schema-sqlite.sql
T = $(sort $(wildcard t[0-9][0-9][0-9][0-9]-*.sh))

check: $(FOREIGN_TARGETS) $(T)

$(FOREIGN_TARGETS):
	$(MAKE) -C $(dir $@) $(notdir $@)

clean:
	$(RM) -r test-results/

$(T):
	@echo "*** $@ ***"; $(SHELL) $@

.PHONY: check $(FOREIGN_TARGETS) clean $(T)
