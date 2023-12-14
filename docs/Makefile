BUILDDIR    = build
SOURCEDIR   = .
SPHINXBUILD = sphinx-build
SPHINXOPTS  = -a -n

.PHONY: help clean

help:
	$(SPHINXBUILD) -M help $(SOURCEDIR) $(BUILDDIR) $(SPHINXOPTS)

clean:
	$(RM) -rv $(BUILDDIR)

%:
	mkdir -pv $(BUILDDIR)
	$(SPHINXBUILD) -M $@ $(SOURCEDIR) $(BUILDDIR) $(SPHINXOPTS) -w $(BUILDDIR)/warnings.log
