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

VERSION = '0.7.4'

class SisDbError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class SisDb(object):

    def __init__(self, client, opts=None):
        self.client = client
        if self.client.version < 1.1:
            raise SisDbError("API Version must be 1.1 or higher.")
        self._schemas = { }
        if client is not None:
            self.refresh(opts)

    def __getattr__(self, name):
        if name in self._schemas:
            return self._schemas[name]

        raise AttributeError

    def available_schemas(self):
        return self._schemas.keys()

    def _add_schema(self, s):
        name = s['name']
        if name not in self._schemas:
            self._schemas[name] = schema.create_schema(self, s)
        else:
            self._schemas[name].update_schema(s)

    def update_schema(self, s):
        name = s['name']
        if name in self._schemas:
            s = self.client.schemas.update(name, s)
            self._schemas[name].update_schema(s)
        else:
            s = self.client.schemas.create(s)
            self._schemas[name] = schema.create_schema(self, s)

    def refresh(self, opts=None):
        schemas = self.client.schemas.fetch_all(opts)
        schema_names = set(map(lambda s : s['name'], schemas))
        my_schemas = set(self._schemas.keys())

        deleted_schema_names = my_schemas - schema_names
        for deleted in deleted_schema_names:
            self._schemas.pop(deleted, None)

        for s in schemas:
            self._add_schema(s)
