#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
from ansible.module_utils.connection import Connection
from ansible.module_utils.six.moves.urllib.parse import urlencode

# -*- coding: utf-8 -*-
#
# (C) Copyright 2020 Hewlett Packard Enterprise Development LP.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied. See the License for the
# specific language governing permissions and limitations
# under the License.

class HttpHelper(object):
    def __init__(self, module):
        self._module = module
        self._connection_obj = None

    @property
    def _connection(self):
        if not self._connection_obj:
            self._connection_obj = Connection(self._module._socket_path)
        return self._connection_obj

    def http_request(self, url, method, data=None):
        return self._connection.send_request(data=data, method=method, path=url)

class AosApi(HttpHelper):
    def __init__(self, module):
        super(AosApi, self).__init__(module)
        self.api_version = "/v1"

    def get_query_params(self):
        query_params = {}
        params = dict(
            config_path=self._module.params.get('config_path'),
            filter=json.dumps(self._module.params.get('filter')),
            sort=self._module.params.get('sort'),
            count=self._module.params.get('count'),
            limit=self._module.params.get('limit'),
            offset=self._module.params.get('offset'),
            total=self._module.params.get('total')
            )
        query_params.update({key: value for key, value in params.items() if value is not None})
        return query_params

    def get_url(self, url, params=None):
        if params:
            return self.api_version + url + '?' +  urlencode(params)
        else:
            return self.api_version + url

    def format_data(self):
        data = None
        params_data = self._module.params.get('data')
        if len(params_data) == 1:
            # data
            data = params_data[0]
        else:
            # multipart data
            data = {'_list': params_data}
        return data

    def write_mem(self):
        config_path = self._module.params.get('config_path')
        url = "/configuration/object/write_memory"
        config_url = self.get_url(url, params={'config_path': config_path})
        result, changed = self.post(url=config_url)
        status = False
        if 'Error' not in result['resp'] and result['code'] == 200:
            status = True
        return status

    def validate_response(self, resp_data):
        res = True
        pending = 0
        status_str = []

        def status_check(resp_data, res):
            # Recursively check status in response data
            # Returns True if all status check passes
            # else return False
            if not res:
                return False
            if isinstance(resp_data, list):
                for ele in resp_data:
                    res = status_check(ele, res)
            elif isinstance(resp_data, dict):
                if "_result" in resp_data.keys():
                    if resp_data["_result"]["status"] != 0:
                        status_str.append(resp_data["_result"]["status_str"])
                        res = False
                for ele, val in resp_data.items():
                    if isinstance(val, (dict, list)):
                        res = status_check(val, res)
            return res

        if "_global_result" in resp_data:
            if resp_data["_global_result"]["status"] == 0:
                res = status_check(resp_data, True)
                if "_pending" in resp_data["_global_result"]:
                    pending = resp_data["_global_result"]["_pending"]
            else:
                res = False

                if "_pending" in resp_data["_global_result"]:
                    pending = resp_data["_global_result"]["_pending"]
                status_str.append(resp_data["_global_result"]["status_str"])
        elif "Error" in resp_data:
            res = False
            status_str.append(resp_data["Error"])

        if status_str:
            status_str = ", ".join(status_str)
        else:
            status_str = ""

        return res, pending, status_str

    def get(self, url, data=None):
        res, code = self.http_request(url=url, method="GET", data=data)
        result = {'resp': res, 'code': code}
        return result

    def post(self, url, data={}):
        data = json.dumps(data)
        config_path = self._module.params.get('config_path')
        idempotency_url = self.get_url('/configuration/object/config',
                                      params={'config_path': config_path})

        # Idemptency logic contributed by author sachaboudjema
        # Description: Check configuration in a node path
        #              before and after config push
        # Date Referenced: May 01 2020
        before = self.get(idempotency_url)['resp']

        res, code = self.http_request(url=url, method="POST", data=data)
        result = {'resp': res, 'code': code}

        after = self.get(idempotency_url)['resp']

        changed = (before != after)

        return result, changed
