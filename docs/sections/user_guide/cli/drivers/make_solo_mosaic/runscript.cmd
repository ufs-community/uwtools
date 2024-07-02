rm -f runscript.make_solo_mosaic
base=../../../../../shared/make_solo_mosaic.yaml
echo "make_solo_mosaic: {run_dir: $PWD}" | uw config realize --input-file $base --update-format yaml --output-file config.yaml
uw make_solo_mosaic runscript --config-file config.yaml 2>/dev/null
cat runscript.make_solo_mosaic
