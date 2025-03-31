rm -rf tmp/answer-alt-schema
uw execute --module answer.py --classname Answer --task answerfile --config-file answer-alt-schema.yaml --schema-file answer-alt-schema.txt
echo The answer is: $(cat tmp/answer-alt-schema/answer.txt)
