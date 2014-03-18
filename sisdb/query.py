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

class Query(object):
    def __init__(self, endpoint, cls):
        self.endpoint = endpoint
        self.cls = cls
        self.query_obj = None
        self._limit = None
        self._offset = None
        self._result = None
        self._total_count = -1

    def _clear_cached_result(self):
        self._result = None
        self._count = -1

    def filter(self, q_obj):
        if not q_obj:
            return self

        if not self.query_obj:
            self.query_obj = { }

        self.query_obj.update(q_obj)
        self._clear_cached_result()

        return self

    def reset(self):
        self.query_obj = None
        self._limit = None
        self._offset = None
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

    def __iter__(self):
        return iter(self.all())

    def count(self):
        if self._count != -1:
            return self._count
        q = { }
        if self.query_obj:
            q['q'] = self.query_obj
        q['limit'] = 1
        page = self.endpoint.list(q)
        self._count = page['total_count']
        return self._count

    def all(self):
        if self._result:
            return self._result

        q = { }
        if self.query_obj:
            q['q'] = self.query_obj
        if self._limit:
            q['limit'] = self._limit
        if self._offset:
            q['offset'] = self._offset

        page = self.endpoint.list(q)
        objs = page['results']
        self._count = page['total_count']
        # convert to data
        self._result = map(lambda o : self.cls(data=o, from_server=True), objs)
        return self._result
