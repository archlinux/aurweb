all: rpc.html

clean:
	rm -rf *.html

%.html: %.txt
	asciidoc $<

.PHONY: all clean
