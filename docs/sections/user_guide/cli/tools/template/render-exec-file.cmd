rm -f rendered
uw template render --input-file template --values-file values.yaml --output-file rendered
cat rendered
