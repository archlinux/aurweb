aur-schema-sqlite.sql: aur-schema.sql
	sed \
		-e 's/ ENGINE = InnoDB//' \
		-e 's/ [A-Z]* UNSIGNED NOT NULL AUTO_INCREMENT/ INTEGER NOT NULL/' \
		-e 's/([0-9, ]*) UNSIGNED / UNSIGNED /' \
		$< >$@

clean:
	rm -rf aur-schema-sqlite.sql

.PHONY: clean
