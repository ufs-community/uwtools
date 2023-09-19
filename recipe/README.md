Do not manually edit `meta.json`.

If `meta.yaml` or `conda_build_config.yaml` (which it depends on) change, regenerate `meta.json` by running `make meta` in the git clone root, from a shell with conda activated and the `condev` package installed (i.e. not a development shell). Commit the updated `meta.json` file.

A `make devshell` command will also automatically update `meta.json` if its dependencies have changed.
