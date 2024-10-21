uw schism --show-schema >schema
if [[ $(grep -c ^ schema) -gt 20 ]]; then
  head schema && echo ... && tail schema
else
  cat schema
fi
