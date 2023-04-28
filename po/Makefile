DESTDIR = ..
PREFIX = /web/locale

POFILES = \
	ar.po \
	ast.po \
	ca.po \
	cs.po \
	da.po \
	de.po \
	el.po \
	es.po \
	es_419.po \
	fi.po \
	fr.po \
	he.po \
	hr.po \
	hu.po \
	it.po \
	ja.po \
	nb.po \
	nl.po \
	pl.po \
	pt_BR.po \
	pt_PT.po \
	ro.po \
	ru.po \
	sk.po \
	sr.po \
	tr.po \
	uk.po \
	zh_CN.po \
	zh_TW.po

MOFILES = ${POFILES:.po=.mo}
LOCALES = ${MOFILES:.mo=}

UPDATEPOFILES = ${POFILES:.po=.po-update}

MSGID_BUGS_ADDRESS = https://gitlab.archlinux.org/archlinux/aurweb/-/issues

all: ${MOFILES}

%.mo: %.po
	msgfmt --check -o $@ $<

%.po-update: %.po aurweb.pot
	lang=`echo $@ | sed -e 's/\.po-update$$//'`; \
	msgmerge -U --no-location --lang="$$lang" $< aurweb.pot

POTFILES-py:
	find ../aurweb -type f -name '*.py' -printf '%P\n' | sort >POTFILES-py

update-pot: POTFILES-py
	pkgname=AURWEB; \
	pkgver=`sed -n 's/version\s*=\s*"\(.*\)"/\1/p' ../pyproject.toml`; \
	xgettext --default-domain=aurweb -L python --join-existing \
		--keyword=translate \
		--add-location=file --add-comments=TRANSLATORS: \
		--package-name="$$pkgname" --package-version="$$pkgver" \
		--msgid-bugs-address='${MSGID_BUGS_ADDRESS}' \
		--directory ../aurweb --files-from POTFILES-py -o aurweb.pot

update-po:
	${MAKE} ${UPDATEPOFILES}

clean:
	rm -f *.mo *.po\~ POTFILES-py

install: all
	for l in ${LOCALES}; do mkdir -p ${DESTDIR}${PREFIX}/$$l/LC_MESSAGES/; done
	for l in ${LOCALES}; do cp $$l.mo ${DESTDIR}${PREFIX}/$$l/LC_MESSAGES/aurweb.mo; done

uninstall:
	for l in ${LOCALES}; do rm -rf ${DESTDIR}${PREFIX}/$$l/LC_MESSAGES/; done

.PHONY: all update-pot update-po clean install uninstall POTFILES-py
