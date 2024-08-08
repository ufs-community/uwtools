rm -rf /tmp/rand-alt
uw execute --module rand.py --classname Rand --task randfile --config-file alt.yaml --schema-file alt.schema
echo Random integer is $(cat /tmp/rand-alt/randint)
