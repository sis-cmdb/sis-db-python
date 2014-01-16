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

class BaseSchema(object):
    def __init__(self, *args, **kwargs):
        self._data = { }
        self._changed = set()
        self._initialized = False
        if 'data' in kwargs:
            data = kwargs['data']
            self.set_data(data)
        self._initialized = True

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self._data == other._data
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def set_data(self, data):
        # get the definition keys
        defn_keys = set(self.__class__.defn.keys())
        data_keys = set(data.keys())
        # clear it
        curr_id = self._data.get('_id', None)
        self._data.clear()
        for k in data_keys.intersection(defn_keys):
            setattr(self, k, data[k])

        if curr_id:
            setattr(self, '_id', curr_id)

    def to_saved_dict(self):
        result = {}
        for k in self._changed:
            val = self._data[k]
            if isinstance(val, BaseSchema):
                val = val.to_saved_dict()
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

            save_data = self.to_saved_dict()

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

        added_keys = new_keys - old_keys
        for k in added_keys:
            setattr(cls, k, field.create_field(new_defn[k], k))

        for k in same_keys:
            curr_field = old_defn[k]
            new_field = new_defn[k]
            if new_field != curr_field:
                setattr(cls, k, field.create_field(new_defn[k], k))

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
        self.root_schema = weakref.proxy(root_schema)
        self.key_name = key_name

    def _mark_as_changed(self, name):
        # tell the root schema that we changed
        self.root_schema._mark_as_changed(self.key_name)

    def to_saved_dict(self):
        result = {}
        for k in self._data:
            val = self._data[k]
            if isinstance(val, BaseSchema):
                val = val.to_saved_dict()
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

    # add id
    attrs['_id'] = field.create_field('objectid', '_id', sisdb, name)
    return type(str(name), (SisSchema,), attrs)
