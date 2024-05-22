out=$(uw rocoto realize --config-file rocoto.yaml --verbose >/dev/null 2>&1)
echo "$out" | head -n10
echo ...
echo "$out" | tail -n10
