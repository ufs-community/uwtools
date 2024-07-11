from testbook import testbook
import os
import yaml

# Run the YAML config section of the notebook
@testbook('./example.ipynb', execute=range(0,4))
def test_get_yaml_config(tb):

   # check output text
   assert tb.cell_output_text(3) == 'values:\n  date: 20240105\n  greeting: Good Night\n  recipient: Moon\n  repeat: 2'
   
   # extract the config_yaml variable from the notebook and test its values
   nb_yaml = tb.ref("config_yaml")
   assert nb_yaml['values'] == {'date': 20240105, 'greeting': 'Good Night', 'recipient': 'Moon', 'repeat': 2}
   
def test_template_render():
   # remove the rendered file if it exists
   rendered_path = "./fixtures/rendered_config.yaml"
   if os.path.exists(rendered_path):
      os.remove(rendered_path)

   # run the template rendering section of the notebook
   with testbook('./example.ipynb', execute=range(4,14)) as tb:

      # check output text of cells with %%bash cell magics
      assert tb.cell_output_text(7) == 'user:\n  name: {{ first }} {{ last }}\n  favorite_food: {{ food }}'
      assert tb.cell_output_text(9) == 'first: John\nlast: Doe\nfood: burritos'
      assert tb.cell_output_text(13) == 'user:\n  name: John Doe\n  favorite_food: burritos'
      
      # check that the rendered file was created in the correct directory
      assert os.path.exists(rendered_path)
      
      # check the contents of the rendered file
      with open(rendered_path, 'r') as f:
         user_config = yaml.safe_load(f)
      assert user_config['user'] == {'name': 'John Doe', 'favorite_food': 'burritos'}

   # clean up the temporary file after the test is run
   os.remove(rendered_path)
   