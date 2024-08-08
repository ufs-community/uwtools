rm -rf /tmp/rand
uw execute --module rand.py --classname Rand --task randfile --config-file rand.yaml --schema-file ./alt.schema
echo Random integer is $(cat /tmp/rand/randint)
