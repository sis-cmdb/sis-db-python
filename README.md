SIS-db-py
=========

ORM like library for SIS

# Install

`python setup.py install`

# Example code

```python

import sispy
import sisdb

# Create an instance of sisdb that uses a SIS client pointing
# to localhost
db = sisdb.SisDb(sispy.Client(url='http://localhost:3000'))

# Schemas are automatically pulled down.  Assuming we have a 'sample' schema with the following JSON:

'''
{
  "definition": {
    "stringField": "String",
    "uniqueNumberField": {
      "unique": true,
      "type": "Number"
    },
    "requiredField": {
      "required": true,
      "type": "String"
    },
    "numberField": "Number",
    "nestedDocument": {
      "nestedBoolean": "Boolean",
      "nestedString": "String"
    },
    "anythingField": {
      "type": "Mixed"
    },
    "owner": [
      "String"
    ]
  },
  "_updated_at": 1389713084168,
  "name": "sample",
  "__v": 0,
  "_id": "52b21c1aaa46430508000003",
  "_created_at": 1387404314635,
  "locked_fields": [],
  "owner": [
    "SIS"
  ],
  "sis_locked": false
}
'''

# Then we can do:

# Get the sample class via db.<schema_name>
Sample = db.sample

# Create an entity
sample_obj = Sample()

# assign some data to basic fields
sample_obj.uniqueNumberField = 20
sample_obj.requiredField = 'sisdb!'

# mixed fields are treated as python dicts
sample_obj.anythingField = { 'foo' : 'bar' }

# nested documents are embedded schemas
sample_obj.nestedDocument.nestedBoolean = True

# List fields work like this
sample_obj.owner.append('SIS')

# save the object
sample_obj.save()

# delete the object
sample_obj.delete()


# Load a sample object by ID
another_obj = Sample.load('some_object_id_here')

# Query objects

samples = Sample.objects().filter({'requiredField' : 'my value'})

# add pagination to the query
samples = samples.limit(1).offset(1)

# iterate the results on the query directly
for s in samples:
    print s.requiredField

# or get as a list of objects
samples = samples.all()

```

# Stuff that's broken / TODO

- handle object ID refs and convert to schema instance object
- client side validation before sending to server
