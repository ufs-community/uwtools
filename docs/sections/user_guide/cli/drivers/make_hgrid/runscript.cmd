rm -f runscript.make_hgrid
base=../../../../../shared/drivers/make_hgrid.yaml
echo "make_hgrid: {rundir: $PWD}" | uw config realize --input-file $base --update-format yaml --output-file config.yaml
uw make_hgrid runscript --config-file config.yaml 2>/dev/null
cat runscript.make_hgrid
