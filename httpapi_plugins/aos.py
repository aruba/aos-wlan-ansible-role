#!/usr/bin/python3
'''
httpapi Ansible plugin to connect with Aruba OS
running on the Mobility Master and Standalone controllers
'''

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

import json
from ansible.module_utils._text import to_text
from ansible.module_utils.connection import ConnectionError
from ansible.module_utils.six.moves.urllib.error import HTTPError
from ansible.plugins.httpapi import HttpApiBase

DOCUMENTATION = """
---
author: Aruba Networks
httpapi: aos
short_description: Use REST to push configs to AOS8 devices
description:
  - This ArubaOS module provides REST interactions with ArubaOS Mobility Master
    and standalone controllers
version_added: 2.8.1
"""

class HttpApi(HttpApiBase):
    def __init__(self, *args, **kwargs):
        super(HttpApi, self).__init__(*args, **kwargs)

    def login(self, username, password):
        path = '/v1/api/login?username='+username+'&password='+password
        method = 'GET'
        self.send_request(data=None, path=path, method=method)

    def logout(self):
        path = '/v1/api/logout'
        data = None
        method = 'GET'
        self.send_request(data=data, path=path, method=method)

    def send_request(self, data, headers={}, **message_kwargs):
        # Ensure Connection
        if not self.connection._connected:
            self.connection._connect()
        if self.connection._auth:
            headers["Cookie"] = self.connection._auth["Cookie"]
            if 'logout' not in message_kwargs['path']:
                sess_tok = self.connection._auth["Cookie"].split("SESSION=")[1]
                message_kwargs['path'] = message_kwargs['path'] + "&UIDARUBA=" + sess_tok

        response, response_data = self.connection.send(data=data, headers=headers,
                                                       path=message_kwargs['path'],
                                                       method=message_kwargs['method'])
        try:
            response_data = json.loads(to_text(response_data.read()))
        except ValueError:
            response_data = response_data.read()
        except AttributeError as arr:
            raise Exception(str(response) + str(arr))
        return self.handle_response(response, response_data)

    def update_auth(self, response, response_text):
        """Return per-request auth token.
        The response should be a dictionary that can be plugged into the
        headers of a request. The default implementation uses cookie data.
        If no authentication data is found, return None
        """
        try:
            cookie = json.loads(to_text(response_text.getvalue()))
            if '_global_result' in cookie.keys():
                if 'UIDARUBA' in cookie['_global_result'].keys():
                    return {'Cookie': "SESSION=" + cookie['_global_result']['UIDARUBA']}
        except Exception as err:
            pass
        return None

    def handle_response(self, response, response_data):
        if isinstance(response, HTTPError):
            if response_data:
                error_text = "Error: " + str(response.code) + ", " + str(response_data)

                raise ConnectionError(error_text, code=response.code)
            raise ConnectionError(to_text(response), code=response.code)

        if response:
            return response_data, response.code

        return response_data, None
