BUILDDIR    = build
SOURCEDIR   = .
SPHINXBUILD = sphinx-build
SPHINXOPTS  = --fail-on-warning --nitpicky --write-all

.PHONY: all help clean docs examples static

all: examples static docs

help:
	$(SPHINXBUILD) -M help $(SOURCEDIR) $(BUILDDIR) $(SPHINXOPTS)

clean:
	$(RM) -rv $(BUILDDIR)

docs:
	$(MAKE) html
	linkchecker --check-extern --no-warnings build/html/index.html

examples:
	COLUMNS=80 $(MAKE) -C sections

static:
	$(MAKE) -C static

%:
	mkdir -pv $(BUILDDIR)
	$(SPHINXBUILD) -M $@ $(SOURCEDIR) $(BUILDDIR) $(SPHINXOPTS) -w $(BUILDDIR)/warnings.log
