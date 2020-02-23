T = $(sort $(wildcard *.t))

check: $(T)

clean:
	$(RM) -r test-results/

$(T):
	@echo "*** $@ ***"; $(SHELL) $@

.PHONY: check $(FOREIGN_TARGETS) clean $(T)
