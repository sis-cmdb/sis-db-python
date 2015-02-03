#############################################################
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
# Copyright (c) 2012-2013 VeriSign, Inc. All rights reserved.
#############################################################

class SisQueryError(Exception):
    def __init__(self, value, *args, **kwargs):
        self.value = value

    def __str__(self):
        return repr(self.value)

class Query(object):
    def __init__(self, endpoint, cls):
        self.endpoint = endpoint
        self.cls = cls
        self.query_obj = None
        self.sort_list = None
        self._limit = None
        self._offset = None
        self._result = None
        self._count = -1
        self._is_all = False
        self._populate = True

    def _clear_cached_result(self):
        self._result = None
        self._count = -1
        self._is_all = False

    def filter(self, q_obj=None, **kwargs):
        if not q_obj and not kwargs:
            return self

        if not self.query_obj:
            self.query_obj = { }

        if q_obj:
            self.query_obj.update(q_obj)

        if kwargs:
            self.query_obj.update(kwargs)

        self._clear_cached_result()

        return self

    # pass in a string 'name' or '-name'
    # or pass in a list ['name','site']
    def sort(self, sort):
        if not sort:
            return self

        if type(sort) != list:
            sort = [sort]
        elif len(sort) == 0:
            return self

        if not self.sort_list:
            self.sort_list = []

        self.sort_list = self.sort_list + sort

        self._clear_cached_result()

        return self

    def reset(self):
        self.query_obj = None
        self._limit = None
        self._offset = None
        self._populate = None
        self._clear_cached_result()
        return self

    def limit(self, lim):
        self._limit = lim
        self._clear_cached_result()
        return self

    def offset(self, off):
        self._offset = off
        self._clear_cached_result()
        return self;

    def populate(self, pop):
        self._populate = pop
        self._clear_cached_result()
        return self

    def __iter__(self):
        return iter(self.all_items())

    def __len__(self):
        return self.count()

    def __getitem__(self, x):
        if self.__len__() < x:
            raise IndexError("Index out of range")
        return self.all_items()[x]

    def count(self):
        if self._count != -1:
            return self._count
        q = { }
        if self.query_obj:
            q['q'] = self.query_obj
        q['limit'] = 1
        page = self.endpoint.fetch_page(q)
        self._count = page._meta.total_count
        return self._count

    def all_items(self):
        if self._result and self._is_all:
            return self._result

        q = { }
        if self.query_obj:
            q['q'] = self.query_obj

        if self.sort_list:
            q['sort'] = ','.join(self.sort_list)

        if not self._populate:
            q['populate'] = False


        items = self.endpoint.fetch_all(q)
        self._is_all = True
        self._count = len(items)
        self._result = map(lambda o : self.cls(data=o, from_server=True), items)
        return self._result

    def bulk_delete(self, query):
        res = self.endpoint.delete_bulk(query)
        self._clear_cached_result()
        return res

    def find_one(self, query=None):
        if query:
            self.filter(q_obj=query)

        q = { }
        if self.query_obj:
            q['q'] = self.query_obj

        q['limit'] = 1

        data = self.endpoint.fetch_page(q)
        count = len(data)
        if count > 1:
            raise SisQueryError("find_one has {count} results".format(count=count))
        elif count == 0:
            return None
        else:
            item = data[0]

        return self.cls(data=item, from_server=True)

    def page(self):
        if self._result:
            if self._is_all:
                # slice
                limit = 200 if self._limit is None else self._limit
                offset = 0 if self._offset is None else self._offset
                return self._result[offset:limit + offset]
            else:
                return self._result

        q = { }
        if self.query_obj:
            q['q'] = self.query_obj
        if self.sort_list:
            q['sort'] = ','.join(self.sort_list)
        if self._limit:
            q['limit'] = self._limit
        if self._offset:
            q['offset'] = self._offset
        if not self._populate:
            q['populate'] = False

        resp = self.endpoint.fetch_page(q)
        self._count = resp._meta.total_count
        # convert to data
        self._result = map(lambda o : self.cls(data=o, from_server=True), resp)
        return self._result
