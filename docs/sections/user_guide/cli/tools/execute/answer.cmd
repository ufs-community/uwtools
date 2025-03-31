rm -rf tmp/answer
uw execute --module answer.py --classname Answer --task answerfile --config-file answer.yaml
echo The answer is: $(cat tmp/answer/answer.txt)
