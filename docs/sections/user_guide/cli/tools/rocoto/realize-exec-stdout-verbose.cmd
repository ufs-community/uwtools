rm -f rocoto.log
uw rocoto realize --config-file rocoto.yaml --verbose >/dev/null 2>rocoto.log
head -n10 rocoto.log
echo ...
tail -n10 rocoto.log
