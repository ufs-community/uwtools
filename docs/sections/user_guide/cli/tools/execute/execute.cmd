rm -rf /tmp/rand
uw execute --module rand.py --classname Rand --task randfile --config-file rand.yaml
ls -l /tmp/rand
cat /tmp/rand/randint
