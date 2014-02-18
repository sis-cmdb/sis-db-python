###########################################################
# The information in this document is proprietary
# to VeriSign and the VeriSign Product Development.
# It may not be used, reproduced or disclosed without
# the written approval of the General Manager of
# VeriSign Product Development.
#
# PRIVILEGED AND CONFIDENTIAL
# VERISIGN PROPRIETARY INFORMATION
# REGISTRY SENSITIVE INFORMATION
#
# Copyright (c) 2013 VeriSign, Inc.  All rights reserved.
###########################################################

import field
import query
import weakref

# sis fields that aren't explicit in definitions
SIS_INTERNAL_FIELDS = {
    '_id' : 'objectid',
    '_created_at' : 'number',
    '_updated_at' : 'number',
    '_updated_by' : 'string',
    '_created_by' : 'string'
}

SIS_INTERNAL_FIELD_NAMES = set(SIS_INTERNAL_FIELDS.keys())

class BaseSchema(object):
    def __init__(self, *args, **kwargs):
        self._data = { }
        self._changed = set()
        self._initialized = False
        if 'data' in kwargs:
            data = kwargs['data']
            self.set_data(data)

        if kwargs.get('from_server', False):
            self._changed.clear()

        self._initialized = True

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self._data == other._data
        elif isinstance(other, dict):
            return self._data == other
        elif isinstance(other, str):
            return other == self._data.get('_id', None)
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def set_data(self, data):
        # get the definition keys
        # make defn_keys the union of the definition and the internal fields
        defn_keys = set(self.__class__.defn.keys()) | SIS_INTERNAL_FIELD_NAMES
        data_keys = set(data.keys())
        # clear it
        curr_id = self._data.get('_id', None)
        self._data.clear()
        for k in data_keys.intersection(defn_keys):
            setattr(self, k, data[k])

        if curr_id:
            setattr(self, '_id', curr_id)

    def _convert_value(self, val):
        if isinstance(val, BaseSchema):
            val = val.to_saved_dict(False)
        elif isinstance(val, list):
            val = map(lambda v: self._convert_value(v), val)
        return val

    def to_saved_dict(self, as_root):
        if not as_root:
            return self._data.get('_id', None)

        result = {}
        for k in self._changed:
            val = self._data[k]
            val = self._convert_value(val)
            result[k] = val
        return result

    @classmethod
    def get_fieldnames(cls):
        defn_keys = set(cls.defn.keys())
        return defn_keys

    def _mark_as_changed(self, name):
        self._changed.add(name)

class SisSchema(BaseSchema):

    def __init__(self, *args, **kwargs):
        super(SisSchema, self).__init__(*args, **kwargs)
        self.root_instance = self
        self.endpoint = self.__class__.db.client.entities(self.__class__.descriptor['name'])

    def save(self):
        if len(self._changed) > 0:
            client = self.__class__.db.client
            if not client:
                self._changed.clear()
                return

            save_data = self.to_saved_dict(True)

            if '_id' in self._data:
                # update
                self._data = self.endpoint.update(self._data['_id'], save_data)
            else:
                self._data = self.endpoint.create(save_data)

            self._changed.clear()
        return self

    def delete(self):
        if '_id' in self._data:
            self.endpoint.delete(self._data['_id'])

        self._data = { }
        self._changed.clear()

    @classmethod
    def load(cls, elem_id):
        return cls(data=cls.db.client.entities(cls.descriptor['name']).get(elem_id))

    @classmethod
    def objects(cls):
        return query.Query(cls.db.client.entities(cls.descriptor['name']), cls)

    @classmethod
    def _update_defn(cls, old_defn, new_defn):
        old_keys = set(old_defn.keys())
        new_keys = set(new_defn.keys())
        removed_keys = old_keys - new_keys
        same_keys = old_keys & new_keys
        for k in removed_keys:
            delattr(cls, k)

        sisdb = cls.db
        name = cls.descriptor['name']
        added_keys = new_keys - old_keys
        for k in added_keys:
            setattr(cls, k, field.create_field(new_defn[k], k, sisdb, name))

        for k in same_keys:
            curr_field = old_defn[k]
            new_field = new_defn[k]
            if new_field != curr_field:
                setattr(cls, k, field.create_field(new_defn[k], k, sisdb, name))

        setattr(cls, 'defn', new_defn)


    @classmethod
    def update_schema(cls, desc):
        if cls.descriptor != desc:
            # make sure the schema gets updated
            if cls.db.client:
                desc = cls.db.client.schemas.update(desc['name'], desc)

            new_defn = desc['definition']
            old_defn = cls.descriptor['definition']
            cls.descriptor = desc
            if old_defn != new_defn:
                cls._update_defn(old_defn, new_defn)

class EmbeddedSchema(BaseSchema):
    def __init__(self, root_schema, key_name, *args, **kwargs):
        super(EmbeddedSchema, self).__init__(args, kwargs)
        if isinstance(root_schema, weakref.ProxyType):
            self.root_schema = root_schema
        else:
            self.root_schema = weakref.proxy(root_schema)
        self.key_name = key_name

    def _mark_as_changed(self, name):
        # tell the root schema that we changed
        self.root_schema._mark_as_changed(self.key_name)

    def to_saved_dict(self, as_root):
        result = {}
        for k in self._data:
            val = self._data[k]
            if isinstance(val, BaseSchema):
                val = val.to_saved_dict(False)
            result[k] = val
        return result


def create_embedded_schema(sisdb, defn, name):
    attrs = {
        'db' : sisdb,
        'defn' : defn
    }

    for k in defn.keys():
        attrs[k] = field.create_field(defn[k], k, sisdb, name)

    return type(str(name), (EmbeddedSchema,), attrs)


def create_schema(sisdb, schema):
    name = schema['name']
    defn = schema['definition']

    attrs = {
        'db' : sisdb,
        'defn' : defn,
        'descriptor' : schema
    }

    for k in defn.keys():
        attrs[k] = field.create_field(defn[k], k, sisdb, name)

    # add sis fields
    for k,v in SIS_INTERNAL_FIELDS.iteritems():
        attrs[k] = field.create_field(v, k, sisdb, name)

    return type(str(name), (SisSchema,), attrs)
