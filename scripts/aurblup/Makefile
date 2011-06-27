include config.mk

SRC = aurblup.c
OBJ = ${SRC:.c=.o}

all: aurblup

config.h:
	cp config.h.proto config.h

${OBJ}: config.h

aurblup: ${OBJ}

install: aurblup
	install -Dm0755 aurblup "${DESTDIR}${PREFIX}/bin/aurblup"
	install -dm0755 "${DESTDIR}/var/lib/aurblup/"

uninstall:
	rm -f "${DESTDIR}${PREFIX}/bin/aurblup"
	rm -f "${DESTDIR}/var/lib/aurblup/"

clean:
	rm -f aurblup ${OBJ}

.PHONY: all install uninstall clean
