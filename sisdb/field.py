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

import schema
import datastructures
import datetime

class SisFieldError(Exception):
    def __init__(self, value, *args, **kwargs):
        self.value = value

    def __str__(self):
        return repr(self.value)

class SisField(object):
    def __init__(self, field_descriptor, *args, **kwargs):
        self.field_desc = field_descriptor

    def __eq__(self, other):
        if isinstance(other, SisField):
            return other.field_desc == self.field_desc
        return False

    def __get__(self, instance, owner):
        if instance is None:
            return self
        res = instance._data.get(self.name, None)
        if hasattr(self, 'to_sis_value'):
            sis_res = self.to_sis_value(res)
            if res != sis_res:
                res = sis_res
                instance._data[self.name] = res
        return res

    def __set__(self, instance, value):
        if (self.name not in instance._data or
            instance._data[self.name] != value):
                instance._mark_as_changed(self.name)
                instance._data[self.name] = value

    def raise_error(self, msg):
        raise SisFieldError(msg)


class BooleanField(SisField):
    def __init__(self, field_descriptor, *args, **kwargs):
        super(BooleanField, self).__init__(field_descriptor, *args, **kwargs)

    def to_sis_value(self, value):
        if value in (True, False):
            return bool(value)
        elif value in ('true', 'True'):
            return True
        elif value in ('false', 'False', None):
            return False
        self.raise_error("Cannot convert to Boolean")

class DateField(SisField):
    def __init__(self, field_descriptor, *args, **kwargs):
        super(DateField, self).__init__(field_descriptor, *args, **kwargs)

    def to_sis_value(self, value):
        if value is None:
            return value
        if (type(value) == datetime.datetime):
            return value
        if (type(value) in [str, unicode]):
            # parse to datetime
            try:
                value = datetime.strptime(value, '%Y-%m-%dT%H:%M:%S.%fZ')
                return value
            except:
                print "value : " + unicode(type(value))
                print 'error parsing ' + unicode(value)
                pass
        self.raise_error("Cannot convert to date")

class NumberField(SisField):
    def __init__(self, field_descriptor, *args, **kwargs):
        super(NumberField, self).__init__(field_descriptor, *args, **kwargs)

    def to_sis_value(self, value):
        if value is None:
            return value
        if type(value) in (int, float):
            return value

        try:
            return int(value)
        except (ValueError, TypeError):
            try:
                return float(value)
            except (ValueError, TypeError):
                self.raise_error("Cannot convert to Number")

class StringField(SisField):
    def __init__(self, field_descriptor, *args, **kwargs):
        super(StringField, self).__init__(field_descriptor, *args, **kwargs)

    def to_sis_value(self, value):
        if value is None:
            return value
        return unicode(value)

class MixedField(SisField):
    def __init__(self, field_descriptor, *args, **kwargs):
        super(MixedField, self).__init__(field_descriptor, *args, **kwargs)

    def __get__(self, instance, owner):
        if instance is None:
            return self
        mix = instance._data.get(self.name, None)
        if not mix or not isinstance(mix, dict):
            instance._data[self.name] = datastructures.BaseDict({}, instance, self.name)
        elif not isinstance(mix, datastructures.BaseDict):
            instance._data[self.name] = datastructures.BaseDict(mix, instance, self.name)

        return instance._data[self.name]

    def __set__(self, instance, value):
        if (self.name not in instance._data or
            instance._data[self.name] != value):
                instance._mark_as_changed(self.name)
                instance._data[self.name] = value

class ListField(SisField):
    def __init__(self, field_descriptor, *args, **kwargs):
        super(ListField, self).__init__(field_descriptor, *args, **kwargs)
        self._inner_field = kwargs.get('field_cls')

    def convert(self, listvalue, instance):
        if not listvalue or not isinstance(listvalue, list):
            return datastructures.BaseList([], instance, self.name, self._inner_field)
        elif not isinstance(listvalue, datastructures.BaseList):
            # ensure vals are the right kind of type
            def convert_value(val):
                if hasattr(self._inner_field, 'convertLazy'):
                    return self._inner_field.convertLazy(val, instance)
                elif hasattr(self._inner_field, 'convert'):
                    return self._inner_field.convert(val, instance)
                return val
            listvalue = map(convert_value, listvalue)
            return datastructures.BaseList(listvalue, instance, self.name, self._inner_field)
        else:
            return listvalue

    def __get__(self, instance, owner):
        if instance is None:
            return self
        listvalue = instance._data.get(self.name, None)
        listvalue = self.convert(listvalue, instance)
        instance._data[self.name] = listvalue
        return instance._data[self.name]

    def __set__(self, instance, value):
        if (self.name not in instance._data or
            instance._data[self.name] != value):
                instance._mark_as_changed(self.name)
                instance._data[self.name] = self.convert(value, instance)

class ObjectIdField(SisField):
    def __init__(self, field_descriptor, *args, **kwargs):
        super(ObjectIdField, self).__init__(field_descriptor, *args, **kwargs)
        self.sisdb = kwargs.get('sisdb')

    def __get__(self, instance, owner):
        if instance is None:
            return self
        val = instance._data.get(self.name, None)
        val = self.convert(val, instance)
        instance._data[self.name] = val

        return instance._data[self.name]

    def to_str(self, value):
        if isinstance(value, str) or isinstance(value, unicode):
            return unicode(value)
        if isinstance(value, dict):
            return value.get('_id', None)
        if hasattr(value, '_id'):
            return value._id
        return value

    def equals(self, o1, o2):
        if o1 == o2:
            return True
        # get ids
        return self.to_str(o1) == self.to_str(o2)

    def convert(self, val, instance):
        return self._convertHelper(val, instance, False)

    def convertLazy(self, val, instance):
        return self._convertHelper(val, instance, True)

    def _convertHelper(self, val, instance, lazy):
        if not val:
            # nothin
            return val

        # check if the object id is a ref..
        ref_type = self.field_desc.get('ref', None)
        if not ref_type:
            # not a ref.. just return
            return val

        # we have a ref.. let's see if it's an object id that needs
        # to load, a dictionary that needs to be converted, or the object itself
        ref_cls = getattr(self.sisdb, ref_type)
        if not ref_cls:
            return val

        if isinstance(val, ref_cls):
            # good to go
            return val
        elif isinstance(val, dict):
            # convert to schema
            val = ref_cls(data=val, from_server=True)
        elif isinstance(val, str) or isinstance(val, unicode):
            if not lazy:
                val = ref_cls.load(val)

        return val

    def __set__(self, instance, value):
        if (self.name not in instance._data or
            instance._data[self.name] != value):
                instance._mark_as_changed(self.name)
                instance._data[self.name] = value

class EmbeddedSchemaField(SisField):
    def __init__(self, schema_desc, *args, **kwargs):
        super(EmbeddedSchemaField, self).__init__(schema_desc, *args, **kwargs)
        schema_desc = schema_desc
        sisdb = kwargs.get('sisdb')
        e_name = kwargs.get('e_name')
        self.schema_cls = schema.create_embedded_schema(sisdb, schema_desc, e_name)

    def __get__(self, instance, owner):
        if instance is None:
            return self

        value = instance._data.get(self.name, None)
        value = self.convert(value, instance)
        instance._data[self.name] = value
        return value

    def __set__(self, instance, value):
        if (self.name not in instance._data or
            instance._data[self.name] != value):
                instance._mark_as_changed(self.name)
                instance._data[self.name] = value

    def convert(self, value, instance):
        if not value:
            value = self.schema_cls(instance, self.name)
        else:
            if isinstance(value, self.schema_cls):
                return value

            if isinstance(value, dict):
                # don't mark as changed.
                vals_dict = value
                value = self.schema_cls(instance, self.name)
                value.set_data(vals_dict)
            else:
                value = self.schema_cls(instance, self.name)
        return value


def create_field_from_string(descriptor, name, sisdb):
    field_types = {
        'number' : NumberField,
        'boolean' : BooleanField,
        'string' : StringField,
        'objectid' : ObjectIdField,
        'ipaddress' : MixedField,
        'mixed' : MixedField,
        'date' : DateField,
    }

    if (type(descriptor) == unicode or
        type(descriptor) == str):
        stype = unicode(descriptor).lower()
        if stype not in field_types:
            raise SisFieldError('Unknown type: %s Field: %s' % (descriptor, name))

        result = field_types[stype]({ 'type' : stype }, sisdb=sisdb)
        result.name = name
        return result

    return None


def create_field(descriptor, name, sisdb, schema_name):
    result = create_field_from_string(descriptor, name, sisdb)

    if result:
        return result

    # embedded document
    if type(descriptor) == dict:
        # could be a proper descriptor with a type
        e_name = '__'.join([schema_name, name])
        desc_type = descriptor.get('type', None)
        if not desc_type:
            # it's a mixed object or inner schema
            if len(descriptor.keys()) == 0:
                # mixed
                result = MixedField(descriptor)
            else:
                # embedded schema
                result = EmbeddedSchemaField(descriptor, sisdb=sisdb, e_name=e_name)
        else:
            # type.. is it a string or an object
            result = create_field_from_string(desc_type, name, sisdb)
            if result:
                result.field_desc.update(descriptor)
                return result

            # type is an object or list
            if type(desc_type) == list:
                inner_name = '__'.join([schema_name, name])
                inner_field = MixedField({ 'type' : 'mixed'})
                if len(desc_type) > 0:
                    inner_field = create_field(desc_type[0], inner_name, sisdb, schema_name)

                result = ListField(desc_type, field_cls=inner_field)
            else:
                # desc_type could actually be the descriptor of a field named
                # type.  yes. pain.
                inner_type = desc_type.get('type', None)
                if type(inner_type) == str or type(inner_type) == unicode:
                    result = EmbeddedSchemaField(descriptor, sisdb=sisdb, e_name=e_name)
                else:
                    # treat desc_type as an embedded schema
                    result = EmbeddedSchemaField(desc_type, sisdb=sisdb, e_name=e_name)

    # array
    elif type(descriptor) == list:
        inner_name = '__'.join([schema_name, name])
        inner_field = MixedField({ 'type' : 'mixed'})
        if len(descriptor) > 0:
            inner_field = create_field(descriptor[0], inner_name, sisdb, schema_name)

        result = ListField(descriptor, field_cls=inner_field)


    if not result:
        raise SisFieldError("Unknown type: %s" % unicode(descriptor))

    result.name = name
    return result
