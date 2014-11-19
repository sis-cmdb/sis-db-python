import unittest
import sispy
import sisdb

class TestSisDb(unittest.TestCase):

    def setUp(self):
        self.client = sispy.Client(url='http://localhost:3000')
        self.client.authenticate('test', 'abc123')
        self.db = sisdb.SisDb(self.client)

    def test_0_refresh_schemas(self):
        schemas = self.db.available_schemas()
        if 'test_sisdb_schema' in schemas:
            self.client.schemas.delete('test_sisdb_schema')
        if 'ref_sisdb_schema' in schemas:
            self.client.schemas.delete('ref_sisdb_schema')
        self.db.refresh()
        schemas = self.db.available_schemas()
        self.assertTrue('test_sisdb_schema' not in schemas)
        self.assertTrue('ref_sisdb_schema' not in schemas)

        # add them
        ref_schema = {
            'name' : 'ref_sisdb_schema',
            'owner' : ['sisdb'],
            'definition' : {
                'ref_name' : "String",
                'type' : 'Number'
            }
        }

        self.db.update_schema(ref_schema)

        schema = {
            'name' : 'test_sisdb_schema',
            'owner' : ['sisdb'],
            'definition' : {
              "name":    "String",
              "living":  "Boolean",
              "age":     { "type" : "Number", "min": 18, "max": 65 },
              "mixed":   "Mixed",
              "nested": {
                "stuff": { "type": "String", "lowercase": True, "trim": True }
              },
              "reference" : {"type" : "ObjectId", "ref" : "ref_sisdb_schema" },
              "enumField" : {"type" : "String", "enum" : ["ONE", "OF", "THESE", "VALUES", "ONLY"]}
            }
        }

        self.db.update_schema(schema)
        self.db.refresh()

        schemas = self.db.available_schemas()

        self.assertTrue('test_sisdb_schema' in schemas)
        self.assertTrue('ref_sisdb_schema' in schemas)


    def test_1_add_entity(self):
        ref_schema = self.db.ref_sisdb_schema
        ref1 = ref_schema()
        ref1.ref_name = 'foo'
        ref1.type = 10
        ref1.save()
        self.assertIsNotNone(ref1._id)

        ref2 = ref_schema()
        ref2.ref_name = "bar"
        ref2.type = 11
        ref2.save()
        self.assertIsNotNone(ref2._id)

        schema = self.db.test_sisdb_schema
        s1 = schema()
        s1.name = "schema"
        s1.living = True
        s1.age = 20
        s1.mixed = {
            "a" : "mixed",
            "object" : ["lives", "here"]
        }
        s1.nested.stuff = "some stuff"
        s1.reference = ref1
        s1.enumField = "ONE"
        s1.save()
        self.assertIsNotNone(s1._id)

    def test_2_get_entities(self):
        ref_schema = self.db.ref_sisdb_schema
        schema = self.db.test_sisdb_schema

        q = ref_schema.objects()
        results = q.all()
        self.assertEqual(len(results), 2)
        self.assertEqual(q.count(), 2)

        q = q.reset().limit(1)
        results = q.all()
        self.assertEqual(len(results), 1)
        self.assertEqual(q.count(), 2)

if __name__ == '__main__':
    unittest.main()
