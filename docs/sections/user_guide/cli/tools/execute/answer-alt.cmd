rm -rf tmp/answer-alt
uw execute --module answer.py --classname Answer --task answerfile --config-file answer-alt.yaml --schema-file answer-alt.schema
echo The answer is: $(cat tmp/answer-alt/answer.txt)
