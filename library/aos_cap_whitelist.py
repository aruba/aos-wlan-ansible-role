
#!/usr/bin/python3
'''
Module for Whitelisting Access Points
'''

# -*- coding: utf-8 -*-

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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: aos_cap_whitelist
version_added: 2.8.1
short_description: Whitelist Campus Access Points (CAP)
description: Module for whitelisting Campus Access Points on the controller under
             the Mobility Master or a Standalone Controller
options:
    action:
        description:
            - Type of action to be performed for whitelisting Campus Acess Points
        require: true
        choices:
            - add
            - delete
        type: str
    ap_name:
        description:
            - Name you would like to give to the the Access Point
        required: false
        type: str
    ap_group:
        description:
            - Name of AP group where the Access Point needs to be added
        required: false
        type: str
    mac_address:
        description:
            - MAC address of the Campus Access Point
        required: true
        type: str
    description:
        description:
            - Short description for the Access Point
        required: false
        type: str

"""
EXAMPLES = """
#Usage Examples
    - name: Whitelist an Access Point to default AP-Group
      aos_cap_whitelist:
       action: add
       ap_name: test-ap-1
       ap_group: default
       mac_address: "ab:32:32:32:32:32"
       description: Boston office, building 6, 2nd floor

    - name: Whitelist an Access Point to configured AP-Group
      aos_cap_whitelist:
       ap_name: test-ap-2
       ap_group: test-ap-group
       mac_address: "zx:32:32:32:32:33"
       description: This is just for testing

    - name: Delete an Access Point from Whitelist
      aos_cap_whitelist:
       action: delete
       mac_address: "ab:32:32:32:32:32"

    - name: Delete an Access Point from Whitelist
      aos_cap_whitelist:
       ap_name: test-ap-2
       ap_group: test-ap-group
       mac_address: "zx:32:32:32:32:33"
       description: This is just for testing



"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.aos_http import AosApi

def main():
    module = AnsibleModule(
        argument_spec=dict(
            action=dict(required=True, type='str', choices=['add', 'delete']),
            ap_name=dict(required=False, type='str'),
            ap_group=dict(required=False, type='str'),
            mac_address=dict(required=True, type='str'),
            description=dict(required=False, type='str')
        ))
    action = module.params.get('action')
    ap_name = module.params.get('ap_name')
    ap_group = module.params.get('ap_group')
    mac_address = module.params.get('mac_address')
    description = module.params.get('description')
    api = AosApi(module)

    if action == 'add':
        config_url = "/v1/configuration/object/wdb_cpsec_add_mac?"
        data = {"description": description, "ap_name": ap_name, "ap_group": ap_group,
                "name": str(mac_address)}

    elif action == 'delete':
        config_url = "/v1/configuration/object/wdb_cpsec_del_mac?"
        data = {"name": str(mac_address)}

    result, changed = api.post(url=config_url, data=data)
    resp = result['resp']
    if resp.has_key("_global_result") and resp["_global_result"]["status"] == 0:
        module.exit_json(changed=changed, response=resp, response_code=result['code'])

    else:
        module.fail_json(changed=False, response=resp, response_code=result['code'],
                         msg=str(resp["_global_result"]["status_str"]))

if __name__ == '__main__':
    main()
