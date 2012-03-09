DESTDIR = ..
PREFIX = /web/locale

POFILES = \
	ca.po \
	cs.po \
	da.po \
	de.po \
	el.po \
	es.po \
	fi.po \
	fr.po \
	he.po \
	hr.po \
	hu.po \
	it.po \
	nb_NO.po \
	nl.po \
	pl.po \
	pt_BR.po \
	pt_PT.po \
	ro.po \
	ru.po \
	sr.po \
	tr.po \
	uk.po \
	zh_CN.po

MOFILES = ${POFILES:.po=.mo}
LOCALES = ${MOFILES:.mo=}

UPDATEPOFILES = ${POFILES:.po=.po-update}

MSGID_BUGS_ADDRESS = https://bugs.archlinux.org/index.php?project=2

all: ${MOFILES}

%.mo: %.po
	msgfmt --check -o $@ $<

%.po-update: %.po aur.pot
	lang=`echo $@ | sed -e 's/\.po-update$$//'`; \
	msgmerge -U --no-location --lang="$$lang" $< aur.pot

update-pot:
	pkgname=AUR; \
	pkgver=`sed -n 's/.*"AUR_VERSION", "\(.*\)".*/\1/p' ../web/lib/version.inc.php`; \
	xgettext --default-domain=aur -L php --keyword=__ --no-location \
		--add-comments=TRANSLATORS: --package-name="$$pkgname" \
		--package-version="$$pkgver" \
		--msgid-bugs-address='${MSGID_BUGS_ADDRESS}' \
		--directory ../web --files-from POTFILES -o aur.pot

update-po:
	${MAKE} ${UPDATEPOFILES}

clean:
	rm -f *.mo *.po\~

install: all
	for l in ${LOCALES}; do mkdir -p ${DESTDIR}${PREFIX}/$$l/LC_MESSAGES/; done
	for l in ${LOCALES}; do cp $$l.mo ${DESTDIR}${PREFIX}/$$l/LC_MESSAGES/aur.mo; done

uninstall:
	for l in ${LOCALES}; do rm -rf ${DESTDIR}${PREFIX}/$$l/LC_MESSAGES/; done

.PHONY: all update-pot update-po clean install uninstall
