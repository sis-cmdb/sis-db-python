# This was grabbed from mongoengine and tweaked for
# our needs.
# https://raw.github.com/MongoEngine/mongoengine/master/mongoengine/base/datastructures.py

import weakref
import schema

class BaseDict(dict):
    """A special dict so we can watch any changes
    """

    _dereferenced = False
    _instance = None
    _name = None

    def __init__(self, dict_items, instance, name):
        if isinstance(instance, weakref.ProxyType):
            self._instance = instance
        else:
            self._instance = weakref.proxy(instance)
        self._name = name
        return super(BaseDict, self).__init__(dict_items)

    def __getitem__(self, *args, **kwargs):
        value = super(BaseDict, self).__getitem__(*args, **kwargs)
        return value

    def __setitem__(self, *args, **kwargs):
        self._mark_as_changed()
        return super(BaseDict, self).__setitem__(*args, **kwargs)

    def __delete__(self, *args, **kwargs):
        self._mark_as_changed()
        return super(BaseDict, self).__delete__(*args, **kwargs)

    def __delitem__(self, *args, **kwargs):
        self._mark_as_changed()
        return super(BaseDict, self).__delitem__(*args, **kwargs)

    def __delattr__(self, *args, **kwargs):
        self._mark_as_changed()
        return super(BaseDict, self).__delattr__(*args, **kwargs)

    def __getstate__(self):
        self.instance = None
        self._dereferenced = False
        return self

    def __setstate__(self, state):
        self = state
        return self

    def clear(self, *args, **kwargs):
        self._mark_as_changed()
        return super(BaseDict, self).clear(*args, **kwargs)

    def pop(self, *args, **kwargs):
        self._mark_as_changed()
        return super(BaseDict, self).pop(*args, **kwargs)

    def popitem(self, *args, **kwargs):
        self._mark_as_changed()
        return super(BaseDict, self).popitem(*args, **kwargs)

    def update(self, *args, **kwargs):
        self._mark_as_changed()
        return super(BaseDict, self).update(*args, **kwargs)

    def _mark_as_changed(self):
        if hasattr(self._instance, '_mark_as_changed'):
            self._instance._mark_as_changed(self._name)


class BaseList(list):
    """A special list so we can watch any changes
    """

    _dereferenced = False
    _instance = None
    _name = None

    def __init__(self, list_items, instance, name, inner_field):
        if isinstance(instance, weakref.ProxyType):
            self._instance = instance
        else:
            self._instance = weakref.proxy(instance)
        self._name = name
        self._inner_field = inner_field
        return super(BaseList, self).__init__(list_items)

    def __contains__(self, item):
        res = super(BaseList, self).__contains__(item)
        if res:
            return res
        num_items = len(self)
        for i in range(0, num_items):
            v = self[i]
            if v == item:
                return True
            if hasattr(self._inner_field, 'equals'):
                res = self._inner_field.equals(v, item)
                if res:
                    return True
        return False

    def __getitem__(self, index, *args, **kwargs):
        value = super(BaseList, self).__getitem__(index)
        if hasattr(self._inner_field, 'convert'):
            new_val = self._inner_field.convert(value, self._instance)
            if type(new_val) != type(value) or new_val != value:
                self[index] = new_val
                value = new_val
        return value

    def __setitem__(self, *args, **kwargs):
        self._mark_as_changed()
        return super(BaseList, self).__setitem__(*args, **kwargs)

    def __delitem__(self, *args, **kwargs):
        self._mark_as_changed()
        return super(BaseList, self).__delitem__(*args, **kwargs)

    def __setslice__(self, *args, **kwargs):
        self._mark_as_changed()
        return super(BaseList, self).__setslice__(*args, **kwargs)

    def __delslice__(self, *args, **kwargs):
        self._mark_as_changed()
        return super(BaseList, self).__delslice__(*args, **kwargs)

    def __getstate__(self):
        self.instance = None
        self._dereferenced = False
        return self

    def __setstate__(self, state):
        self = state
        return self

    def append(self, *args, **kwargs):
        self._mark_as_changed()
        return super(BaseList, self).append(*args, **kwargs)

    def extend(self, *args, **kwargs):
        self._mark_as_changed()
        return super(BaseList, self).extend(*args, **kwargs)

    def insert(self, *args, **kwargs):
        self._mark_as_changed()
        return super(BaseList, self).insert(*args, **kwargs)

    def pop(self, *args, **kwargs):
        self._mark_as_changed()
        return super(BaseList, self).pop(*args, **kwargs)

    def remove(self, *args, **kwargs):
        self._mark_as_changed()
        return super(BaseList, self).remove(*args, **kwargs)

    def reverse(self, *args, **kwargs):
        self._mark_as_changed()
        return super(BaseList, self).reverse(*args, **kwargs)

    def sort(self, *args, **kwargs):
        self._mark_as_changed()
        return super(BaseList, self).sort(*args, **kwargs)

    def _mark_as_changed(self, name=None):
        if hasattr(self._instance, '_mark_as_changed'):
            self._instance._mark_as_changed(self._name)
