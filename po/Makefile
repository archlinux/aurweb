DESTDIR = ..
PREFIX = /web/locale

POFILES = \
	ca.po \
	cs.po \
	da.po \
	de.po \
	el_GR.po \
	es.po \
	fr.po \
	he.po \
	hr.po \
	hu.po \
	it.po \
	nb_NO.po \
	pl.po \
	pt.po \
	ro.po \
	ru.po \
	sr.po \
	tr.po \
	uk.po \
	zh_CN.po

MOFILES = ${POFILES:.po=.mo}
LOCALES = ${MOFILES:.mo=}

all: ${MOFILES}

%.mo: %.po
	msgfmt -o $@ $<

clean:
	rm *.mo

install: all
	for l in ${LOCALES}; do mkdir -p ${DESTDIR}${PREFIX}/$$l/LC_MESSAGES/; done
	for l in ${LOCALES}; do cp $$l.mo ${DESTDIR}${PREFIX}/$$l/LC_MESSAGES/aur.mo; done

uninstall:
	for l in ${LOCALES}; do rm -rf ${DESTDIR}${PREFIX}/$$l/LC_MESSAGES/; done

.PHONY: all clean install uninstall
