# Language
If you have ever written web pages, you must have come across HTML forms and the need to validate the input when the user clicks the **Ok** button. The Language module, in its most simple form implements just that: validating a the contents of a form based on a configuration defining what is valid.

The Language module does extend the functionality to provide advanced feature that will both:
* simplify the textual interface for the end-user
* curate and simplify the data for the developer.

## Definitions
Let us assume that our *form* is contained in a Python dictionary.

### Schema
A **schema** is a Python dictionary that defines which fields (or keywords) are required, which ones are optional, which ones have a default values, what type a field has, etc... It defines the semantics of the Python dictionary (the *form*).

A **schema** has itself a schema, a Python dictionary that is a collection of valid keywords (or fields) to define a schema. The schema part of it defines attributes of the schema:
```python
schema = {
    'schema': {
        'type': str,
        'required': True
    },
    'items': {
        'type': dict,
        'required': True
    },
    'ignore_unknown_keywords': {
        'type': bool,
        'required': False,
        'default': False
    },
    'help': {
        type: str,
        'required': False
    },
    'inherit': {
        'required': False,
        'unique': False
    },
    'merge': {
        # [ field1, field2, ... ]
        # the contents of the field should correspond
        # to the name of a schema in the schema directory
        'required': False,
        'unique': False
    }
}
```
The item part of the schema defined which fields (or keywords) are recognised and their properties:
```python
item = {
        'required': {
            'required': False,
            'default': True,
            'type': bool,
            'show_in_help': True
        },
        'unique': {
            'required': False,
            'default': True,
            'type': bool,
            'show_in_help': True
        },
        'lowercase': {
            'required': False,
            'default': False,
            'type': bool,
            'show_in_help': False
        },
        'validate': {
            'required': False,
            'type': list,
            'show_in_help': True
        },
        'default': {
            'required': False,
            'show_in_help': True
        },
        'type': {
            'required': False,
            'show_in_help': True
        },
        'delete': {
            'required': False,
            'default': False,
            'show_in_help': False
        },
        'help': {
            'required': False,
            'show_in_help': False
        },
        'schema': {
            'required': False,
            'show_in_help': True
        },
        'excludes': {
            'required': False,
            'show_in_help': True,
            'type': list
        },
        'alias': {
            'required': False,
            'type': list,
            'show_in_help': True
        },
        'derived': {
            'required': False,
            'show_in_help': True
        }
    }
}
```
Please check the [source code](https://github.com/JCSDA-internal/solo/blob/develop/src/solo/language/schema_validate.py) for the latest definitions.

### Schema directory
When initialising the Language, you define a **schema directory**, this is a directory where all the schemas for a particular application are stored. Schemas can be stored in any file format that can produce a Python dictionary, the YAML and JSON formats are provided by default, you can write your own schema reader if necessary. Within the schema directory, a schema file name is expected to be the schema name with the file extension.

We recommend using YAML files as its syntax is leaner than JSON's.

### Directives
Since the language module can validate any Python dictionary, that dictionary can come from anywhere, for example, from a YAML configuration file, see [solo.configuration](https://github.com/JCSDA-internal/solo/blob/develop/src/solo/configuration/configuration.py). However, when providing an end-user with a textual interface, using Python itself to deal with syntax and grammar analysis will save you a lot of development and maintenance time. This is why the [Directive class](https://github.com/JCSDA-internal/solo/blob/develop/src/solo/language/directive.py) exists.

The Directive class inherits from dict. You may have heard that inheriting from dict can be dangerous and should not be done, but as long as you don't alter the behaviour of the **update** and **setdefault** methods, you are ok. The dictionary constructor syntax using named args, provides the end-user with a nicely sugared syntax.

When using the Directive class, the Language module expects the schema associated with a Directive to have the name of the Directive subclass in lower case, for example if your subclass is called Person, the schema will be expected to be called person.yaml (YAML being the default format). If you want to force the schema name to be different, you need to define a class variable called \_\_schema__ to define the name of the schema.

Directive inherits from [solo.nice_dict.NiceDict](https://github.com/JCSDA-internal/solo/blob/develop/src/solo/nice_dict.py) which provides a prettified print of the dictionary and enables dictionary keys to be accessed like members of the class, for example:
```python
from solo.nice_dict import NiceDict

d = NiceDict()
d['one'] = 1
d['two'] = 2
d['twelve'] = 12
d['thirteen'] = 13
print(d)
print(d.one)
print(d.twelve, d['twelve'])
```
*Output:*
```bash
    one:            1
    thirteen:       13
    twelve:         12
    two:            2
1
12 12
```

# Introductory examples

Let's imagine that we want to capture someone's firstname, surname and age and provide the user with a dictionary-like textual interface provided by the Directive. We need to define:
* a schema
* a class that will capture the data

For simplicity, in this example and all the following ones, we assume that you have solo installed on your machine (preferably in a virtual environment in order to not pollute your Python installation).

we create a directory called schema_1 and create a schema file schema_1/person.yaml that looks like this:
```yaml
schema: person
items:
  firstname:
  surname:
  age:
```
By defining *empty dictionaries* (that are returned as None by pyyaml), we state that we want the default attributes for our keyword, if you check the [source code](https://github.com/JCSDA-internal/solo/blob/develop/src/solo/language/schema_validate.py):

| Keyword | Value  | Action
 :-------- | :-------| :-------|
| required | True  | Will raise an exception if not present
| unique   | True  | Will raise an exception if a list is given
| lowercase | False | Will force string to lower case
| uppercase | False | Will force string to upper case
| validate | Not specified | no action
| default  | No default value | no action
| type     | No type specified | the type given is kept

Let's ignore the rest for now. Let us write some code:

```python
from solo.language import Directive

class Person(Directive):
    def __init__(self, *args, **kwargs):
        super().__init__('./schema_1', *args, **kwargs)

person = Person(
    firstname = 'John',
    surname = 'Doe',
    age = 42
)
print(type(person.age))
```
*Output:*
```bash
person
    age:            42
    firstname:      John
    surname:        Doe
<class 'int'>
```
Let's assume that we will use this in a SQL query and we would rather have the age as a string. We would also like to add the department in which that person is employed and optionally the firstname of their children. We change the schema:
```yaml
schema: person
items:
  firstname:
  surname:
  age:
    type: string
  department:
  children:
    required: false
    # we want this to be a list
    unique: false
```
*Running the same program, outputs:*
```bash
2020-11-07 16:02:01,257 - ERROR - solo.language.language - Required keyword(s) are missing in person: department
```
Only department is required.
Modifying the program:
```python
from solo.language import Directive

class Person(Directive):
    def __init__(self, *args, **kwargs):
        super().__init__('./schema_1', *args, **kwargs)

person = Person(
    firstname = 'John',
    surname = 'Doe',
    age = 42,
    department = 'accounting',
    chilren = ['Joey', 'Amelia']
)
```
```bash
person
    age:            42
    children:       
                 Joey
                 Amelia
    department:     accounting
    firstname:      John
    surname:        Doe
<class 'str'>
```
We can see that the age is now a string.

Finally, to show a few more features:
```yaml
schema: person
items:
  firstname:
  surname:
  age:
    type: string
  department:
    validate: [ set-choices, accounting, sales, marketing, warehouse ] # new
    alias: service # new
  children:
    required: false
    unique: false
  full_time:
    type: boolean
    default: yes # new
```
The main script is:
```python
from solo.language import Directive
  
class Person(Directive):
    def __init__(self, *args, **kwargs):
        super().__init__('./schema_1', *args, **kwargs)
        print(self)

person = Person(
    firstname = 'John',
    surname = 'Doe',
    age = 42,
    service = 'accounting',
    children = ['Joey', 'Amelia']
)
```
*Output:*
```bash
person
    age:            42
    children:       
                 Joey
                 Amelia
    department:     accounting
    firstname:      John
    full_time:      True
    surname:        Doe
```
The newly introduced keywords:
* **default**: gives the field a default value and therefore makes it not required. Please note the boolean type can hold True, yes or y, False, no or n.
* **alias**: can be a list of aliases to enable to have alternate names for a field or shorter names. The dictionary is always expanded with the original name of the field.
* **validate**: provides a limited choice of values that can be input. You can write your own validators.

# Nesting Schemas

You can nest dictionaries and make sure that the Language module validates each of them. At this point we have two different scenarios.

## Nesting Directives

Nesting directives is easy provided all classes involved inherit from Directive. Let's see a quick example of adding an office location for our Person(s):
```python
from solo.language import Directive

class Office(Directive):
    def __init__(self, *args, **kwargs):
        super().__init__('./schema_1', *args, **kwargs)
```
```yaml
schema: office
items:
    number:
    floor:
```
The schema for person becomes:
```yaml
schema: person
items:
  firstname:
  surname:
  age:
    type: string
  department:
    validate: [ set-choices, accounting, sales, marketing, warehouse ]
    alias: dep
  children:
    required: false
    unique: false
  full_time:
    type: boolean
    default: yes
  office:
```
The program becomes:
```python
person = Person(
    firstname = 'John',
    surname = 'Doe',
    age = 42,
    dep = 'accounting',
    children = ['Joey', 'Amelia'],
    office = Office(
        number = 232,
        floor = 2
    )
)
```
*Output:*
```bash
person
    age:            42
    children:       
                 Joey
                 Amelia
    department:     accounting
    firstname:      John
    full_time:      True
    office:         
        floor:          2
        number:         232
    surname:        Doe

```
The **office** nested dictionary is validated against its schema.

## Nesting Configuration Dictionaries
When it comes to configuration, the dictionary is read directly from a YAML (or other format) file. We still need to tell the Language module to check the nested dictionary against a schema:
config.yaml:
```yaml
name: 'myConfig'
files: 12
network: 'eth0'
hosts:
  backup: 123.456.789.123
```
We want the hosts sub-dictionary to be checked. We create the schemas in the schema_2 directory:

schema_2/config.yaml:
```yaml
schema: config
items:
    name:
    files:
      type: int
    network:
    hosts:
      schema: hosts
```
schema_2/hosts.yaml:
```yaml
schema: hosts
items:
  main:
    default: localhost
  backup:
```
config.py
```python
from solo.configuration import Configuration
  
config = Configuration('config.yaml', 'schema_2', 'config')
print(config)
```
*Output:*
```bash
    files:          12
    hosts:          
        backup:         123.456.789.123
        main:           localhost
    name:           myConfig
    network:        eth0
```

# Schema Manipulation

We have seen so far a form validation system (glorified because of some improvements). We would, however like to save the programmer some work and mostly make life easier to the end-user.

We are going to work with an example of geometrical shapes in this section.

## Inheritance

Just as well as object oriented inheritance, schema inheritance can provide the programmer with a powerful tool to reduce the size of schema files and enforce consistency between different directives.

We are going to represent geometrical shapes, a circle, a rectangle and a square. All shape have coordinates on a plane and a column. This can be represented with a schema:
schema_3/shape.yaml
```yaml
schema: shape
items:
  x:
    type: int
  y:
    type: int
  colour:
    default: black
```

The rectangle inherits from shape:
schema_3/rectangle.yaml
```yaml
schema: rectangle
inherit: shape
items:
  length:
    type: int
  width:
    type: int
```

So do the square and the circle:
schema_3/square.yaml
```yaml
schema: square
inherit: shape
items:
  side:
    type: int
```

schema_3/circle.yaml
```yaml
schema: circle
inherit: shape
items:
  radius:
    type: int
```

rectangle.py
An example:
```python
from solo.language import Directive
  
class Rectangle(Directive):
    def __init__(self, *args, **kwargs):
        super().__init__('./schema_3', *args, **kwargs)
        print(self)

if __name__ == '__main__':
    r = Rectangle(
        x = 12,
        y = 145,
        colour = 'yellow',
        length = 15,
        width = 10
    )     
```

*Output:*
```bash
rectangle
    colour:         yellow
    length:         15
    width:          10
    x:              12
    y:              145
```

The **inherit** keyword is used to name a schema that is to be found in the schema directory. It can be a list of schema names (multiples inheritance).

Inheritance is handled as such, if schema is our current schema and parent is the schema we inherit from, schema will inherit from parent all fields (item names) and properties (unique, required, etc..) from the parent that are not already in schema. Let's look at an exmaple:

```yaml
schema: parent
items:
  married:
    type: boolean
    default: yes

schema: schema
inherit: parent
items:
  married: {}
```
The final schema is:

```yaml
schema: schema
items:
  married:
    type: boolean
    default: yes
```

Using:

```yaml
schema: parent
items:
  married:
    type: boolean
    default: yes

schema: schema
inherit: parent
items:
  married: 
     default = no
```

The final schema is:

```yaml
schema: schema
items:
  married:
    type: boolean
    default: no
```


## Merging Schemas

Let's imagine that in some instances we would like to handle shapes in a 2D system and other times in a 3D system. This means that for managing 3D we need to add a z coordinate. One way to do it would be to have a shape2D and a shape3D schema, and have shapes inheriting from them. That would double the number of schemas and classes to write. The solution is to *merge schemas dynamically* based on the value of fields in the directive. Merging is similar to inheritance except that the rules of inheritance work the other way around: The schema we merge into, inherits the fields and properties of the current schema.

Our shapes in 2D and 3D now become:
```yaml
schema_3/shape.yaml
schema: shape
merge: dimension
items:
  colour:
    default: black
  dimension:
    default: 2d
    validate: [ set-choices, 2d, 3d ]

schema_3/2d.yaml
schema: 2d
items:
  x:
    type: int
  y:
    type: int

schema_3/3d.yaml
schema: 3d
inherit: 2d
items:
  z:
    type: int
```
Running rectangle.py produces:
```bash
rectangle
    colour:         yellow
    dimension:      2d
    length:         15
    width:          10
    x:              12
    y:              145
```
If we modify rectangle.py:
```python
from solo.language import Directive
  
class Rectangle(Directive):
    def __init__(self, *args, **kwargs):
        super().__init__('./schema_3', *args, **kwargs)
        print(self)

r = Rectangle(
    x = 12,
    y = 145,
    colour = 'yellow',
    length = 15,
    width = 10,
    dimension = '3d'
)
```
Executing this:
```bash
2020-11-08 19:44:07,846 - ERROR - solo.language.language - Required keyword(s) are missing in rectangle: z
```
After adding z = 11:
```bash
rectangle
    colour:         yellow
    dimension:      3d
    length:         15
    width:          10
    x:              12
    y:              145
    z:              11
```
Merging enables the creation of **dynamic schemas** that are modified depending on values in the Directive. Using this feature, we could simplify the concept of shape to one single class:
```yaml
schema: shape
merge:
  - dimension
  - shape
items:
  colour:
    default: black
  dimension:
    default: 2d
    validate: [ set-choices, 2d, 3d ]
  shape:
```
In each other schema, circle.yaml, rectangle.yaml and square.yaml we removed the statement: *inherit: shape* (otherwise we would end up in an infinite recursion).

shape.py
```python
from solo.language import Directive
  
class Shape(Directive):
    def __init__(self, *args, **kwargs):
        super().__init__('./schema_3', *args, **kwargs)
        print(self)

r = Shape(
    shape = 'circle',
    x = 12,
    y = 145,
    colour = 'yellow',
    radius = 5
)
```
*Outputs:*
```bash
shape
    colour:         yellow
    dimension:      2d
    radius:         5
    shape:          circle
    x:              12
    y:              145
```

### Schema Specialization

While the merging of schemas is a powerful mechanism, sometimes thing can become complicated and you want to handle special cases.

# Customising

It is possible to enrich the functionality of the Language module.

## Adding Types

All the python builtin types (that are defined in the builtin module are supported automatically). Please see the Types module to see existing added types. Some useful types:

| Type | Comment |
|------|---------|
| big_number | Adds comas to a large number, 1000000 -> 1,000,000 |
| date | Converts a date 2020-01-01 a solo.date.Day object |
| boolean | Converts the value to a Boolean, takes True, yes, y, False, no, no
| path | Substitutes environment variable in the form ${NAME} in the string
| include | Interpret the value as a path to a yaml file and reads the file
| duration | Convert the input to seconds. Takes 10s 1h 1d 2d6h7mn, 12 minutes etc...
| iso_duration | Interprets the string a an iso 8601 duration and converts to solo.Date.DateIncrement (e.g. P1D03H)

### Adding you own type

The **Type** class is a factory, all you need to do is provide a class of a function that receive the value input in the Directive by the end-user and returns the value converted to the type you are implementing.

```python
from solo.language import Types

class MySpecialType:

    def __init__(self, value):
        self._value = value

def to_my_special_type(value):
    return MySpecialType(value)

Types.register('my_special_type', to_my_special_type)
```
Make sure the file containing this code is imported in your application, once registered it is recognised by Language.

## Adding Validators

Validators are described using the keyword **validate** and a dictionary. The first element of the dictionary is the name of the validator, the following arguments (*args) can be anything you decide. This notation was designed this way to keep the syntax simpler in the yaml file.

Most of the time, validators are expected to validate the value of a keyword in the directive, based on extra arguments and decide whether this is valid (return the value in the directive) or raise a ValueError exception.

Example:
```python
from solo.language import Validate

class ValidateInterval:
    
    def __init__(self, *args):
        """
            We decides that args is a tuple of two integer, 
            the first is the lower bound (included) 
            and the second is the higher bound (not included)
        """
        self._low, self._high = list(args)[:2] 

    def __call__(self, keyword, request):
        """
            - keyword if the keyword the validate is
              associated with
            - request is a dictionary containing the directive
              in its current state of processing. You have no
              guarantee that a particular keyword has been
              processed yet
        """
        value = request[keyword]
        if value < self._low or value >= self._high:
            raise ValueError(f'Value is out of bounds: {self._low} <= {value} < {self._high}')
        return request[keyword]

Validate.register('interval', ValidateInterval)
```
The syntax in the yaml file would be:
```yaml
schema: example
items:
    temperature:
        type: float
        validate: [ interval, 13.2, 27.8 ]
```

Since the **\_\_call__** method returns the value in the request for the keyword, it is also possible to "correct" the value. In this case if the value is below the minimum it could be brought up to the minimum, same for the max value. In that case, no exceptions needs to be raise.

# Finally

Please check the [unit tests](https://github.com/JCSDA-internal/solo/blob/develop/src/tests/test_language.py) in the solo package.