BUILDDIR    = _build
SOURCEDIR   = .
SPHINXBUILD = sphinx-build
SPHINXOPTS  = -n

# .PHONY: help Makefile
.PHONY: help

help:
	$(SPHINXBUILD) -M help $(SOURCEDIR) $(BUILDDIR) $(SPHINXOPTS) $(O)

# clean:
# 	$(RM) -f $(BUILDDIR)/*

# %: Makefile
%:
	mkdir -pv $(BUILDDIR)
	$(SPHINXBUILD) -M $@ $(SOURCEDIR) $(BUILDDIR) $(SPHINXOPTS) -w $(BUILDDIR)/warnings.log
