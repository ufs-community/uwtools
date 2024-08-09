rm -rf /tmp/rand
uw execute --module rand.py --classname Rand --task randfile --config-file rand.yaml
echo Random integer is $(cat /tmp/rand/randint)
