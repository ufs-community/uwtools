BUILDDIR    = build
SOURCEDIR   = .
SPHINXBUILD = sphinx-build
SPHINXOPTS  = --fail-on-warning --nitpicky --write-all

.PHONY: help clean docs examples

help:
	$(SPHINXBUILD) -M help $(SOURCEDIR) $(BUILDDIR) $(SPHINXOPTS)

clean:
	$(RM) -rv $(BUILDDIR)

docs:
	$(MAKE) html
	linkchecker --check-extern --no-warnings --user-agent Mozilla/5.0 build/html/index.html

examples:
	COLUMNS=80 $(MAKE) -C sections

%:
	mkdir -pv $(BUILDDIR)
	$(SPHINXBUILD) -M $@ $(SOURCEDIR) $(BUILDDIR) $(SPHINXOPTS) -w $(BUILDDIR)/warnings.log
