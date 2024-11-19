BUILDDIR     = build
SOURCEDIR    = .
SPHINXBUILD  = sphinx-build
SPHINXOPTS   = -a -n -W --keep-going

.PHONY: help clean docs examples

help:
	$(SPHINXBUILD) -M help $(SOURCEDIR) $(BUILDDIR) $(SPHINXOPTS)

clean:
	$(RM) -rv $(BUILDDIR)

docs:
	$(MAKE) html
	linkchecker --check-extern --no-warnings build/html/index.html

examples:
	COLUMNS=80 $(MAKE) -C sections

%:
	mkdir -pv $(BUILDDIR)
	$(SPHINXBUILD) -M $@ $(SOURCEDIR) $(BUILDDIR) $(SPHINXOPTS) -w $(BUILDDIR)/warnings.log
