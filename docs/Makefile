BUILDDIR     = build
LINKCHECKDIR = $(BUILDDIR)/linkcheck
SOURCEDIR    = .
SPHINXBUILD  = sphinx-build
SPHINXOPTS   = -a -n -W

.PHONY: help clean docs examples linkcheck

help:
	$(SPHINXBUILD) -M help $(SOURCEDIR) $(BUILDDIR) $(SPHINXOPTS)

clean:
	$(RM) -rv $(BUILDDIR)

docs:
	$(MAKE) linkcheck
	$(MAKE) html

examples:
	$(MAKE) -C sections

linkcheck:
	$(SPHINXBUILD) -b linkcheck $(SPHINXOPTS) -c $(CURDIR) $(CURDIR) build/linkcheck

%:
	mkdir -pv $(BUILDDIR)
	$(SPHINXBUILD) -M $@ $(SOURCEDIR) $(BUILDDIR) $(SPHINXOPTS) -w $(BUILDDIR)/warnings.log
