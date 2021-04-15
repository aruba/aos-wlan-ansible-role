
#!/usr/bin/python3
'''
Module for passing show commands over AOS8 REST API
'''

# -*- coding: utf-8 -*-

# (C) Copyright 2020 Hewlett Packard Enterprise Development LP.

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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: aos_show_command
version_added: 2.8.1
short_description: Fetch show commands output using API
description: A special GET request for using show commands on the Mobility Conductor or a Standalone Controller
             to get the response using API
options:
    command:
        description:
            - CLI show command that runs on the mynode of Mobility Conductor,
              Standalone Controller (md) depending on where the
              information you are looking for exists.
            - Make sure to use the correct show command.
            - Most of the show commands will fetch a JSON formated output
        require: true
        type: str

"""
EXAMPLES = """
#Usage Examples
    - name: Show command for fetching AP database
      aos_show_command:
       command: show ap database

    - name: Show command for fetching Web Server Profile
      aos_show_command:
       command: show web-server profile
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.aos_http import AosApi

def main():
    module = AnsibleModule(
        argument_spec=dict(
            command=dict(required=True, type='str')
        ))
    command = module.params.get('command')
    api = AosApi(module)
    query_url = "/configuration/showcommand"
    query_params = {"command": command}
    request = api.get_url(query_url, params=query_params)
    result = api.get(url=request)
    if len(result['resp']) < 1:
        module.exit_json(changed=False, msg=result['resp'], response="Empty response received."
                                            " Check if a valid show command"
                                            " is given in the playbook.")
    elif result['resp'] is not None:
        module.exit_json(changed=False, msg=result['resp'], response_code=result['code'])
    else:
        module.fail_json(changed=False, msg="Failed !!!", response_code=result['code'])

if __name__ == '__main__':
    main()
