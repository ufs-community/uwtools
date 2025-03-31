rm -rf tmp/answer-alt
uw execute --module answer.py --classname Answer --task answer --config-file alt.yaml --schema-file alt.schema
echo The answer is: $(cat tmp/answer-alt/answer.txt)
