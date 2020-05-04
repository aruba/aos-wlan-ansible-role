
#!/usr/bin/python3
'''
Module for changing vlan configuration
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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: aos_vlan
version_added: 2.8.1
short_description: Configure VLAN IDs on ArubaOS products like Mobility Master
                   and Mobility Controllers using AOS APIs
description: Module for creating and deleting VLAN IDs and getting a list of
             configured VLAN IDs on the Mobility Master and Mobility Controllers
options:
    vlan_name:
        description:
            - Name given to a Named VLAN
              Example: User-VLAN
              Example: Mgmt-VLAN
        required: false
        type: str
    vlan_id:
        description:
            - VLAN ID/IDs or ranvge of VLANs to be configured.
              Example: 5
              Example: 5,10
              Example: 5,10,15-20
        required: false
        type: str
    config_path:
        description:
            - Path in configuration hierarchy to the node the API call is applied to
              On managed device this will be restricted to /md, while on a
              stand-alone controller, this will be restricted to /mm and /mm/mynode.
        required: false
        type: str
    action:
        description:
            - An action to get, create and delete VLANs or Named VLANs
        required: true
        choices:
            - get
            - create
            - delete
        type: str
    type:
        description:
            - Type of VLAN to be retrieved during GET operation.
        required: true
        choices:
            - all
            - named_vlan
        type: str
"""
EXAMPLES = """
#Usage Examples
    - name: Create a VLAN
      aos_vlan:
       action: create
       vlan_id: 5
       config_path: /md/Boston

    - name: Create multiple VLANs
      aos_vlan:
       action: create
       vlan_id: 5,10, 15-20
       config_path: /md/Boston

    - name: Create a named VLAN
      aos_vlan:
       action: create
       vlan_name: User-VLAN
       vlan_id: 5
       config_path: /md/Boston

    - name: Create multiple VLANs under a named VLAN
      aos_vlan:
       action: create
       vlan_name: User-VLANs
       vlan_id: 5,10-15
       config_path: /md/Boston

  *********************************************************************************
  NOTE: Playbook for creating Named VLANs with vlan_name parameter in the playbook
        will over-ride existing configuration if named VLAN with the same name
        exists.However, if done so, existing VLANs under the named VLAN will become
        unnamed.
  *********************************************************************************

    - name: Delete a named VLAN and VLANs under the named VLAN (2 tasks)
      aos_vlan:               #STEP-1 Delete name and ID mapping of the named VLAN
       action: delete
       vlan_name: User-VLAN
       config_path: /md/Boston
    - aos_vlan:               #STEP-2 Delete the VLANs configured under above named VLAN
       action: delete
       vlan_id: 5,10-15
       config_path: /md/Boston

    - name: Delete multiple VLANs
      aos_vlan:
       action: delete
       vlan_ids: 5,10
       config_path: /md/Boston

    - name: Delete multiple VLANs
      aos_vlan:
       action: delete
       vlan_ids: 15-20
       config_path: /md/Boston

    - name: Get a list of named vlans
      aos_vlan:
       action: get
       type: named_vlan
       config_path: /md/Boston

    - name: Get a list of all VLANs from current as well as parent hierarchy
      aos_vlan:
       action: get
       type: all
       config_path: /md/Boston


"""
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.aos_http import AosApi

def get_vlan_list(vlan_id):
    vlan_id = vlan_id.replace(" ", "")
    vlan_id_list = sum(((list(range(*[int(b) + c for c, b in enumerate(a.split('-'))]))
                         if '-' in a else [int(a)]) for a in vlan_id.split(',')), [])
    return vlan_id_list

def main():
    module = AnsibleModule(
        argument_spec=dict(
            vlan_name=dict(required=False, type='str'),
            vlan_id=dict(required=False, type='str'),
            config_path=dict(required=True, type='str'),
            action=dict(required=False, type='str', choices=['get', 'create', 'delete']),
            type=dict(required=False, type='str', choices=['all', 'named_vlan'], default='all')
        ))
    vlan_name = module.params.get('vlan_name')
    vlan_id = module.params.get('vlan_id')
    action = module.params.get('action')
    type_vlan = module.params.get('type')
    config_path = module.params.get('config_path')
    api = AosApi(module)
    config_url = "/v1/configuration/object/vlan_id?config_path=" + str(config_path)

    if action == "create":
        if vlan_name:
            config_url = "/v1/configuration/object?config_path=" + str(config_path)
            data = {"vlan_name": [{"_action": "modify", "name": vlan_name}],
                    "vlan_range": {"_action": "modify", "WORD": vlan_id.replace(" ", "")},
                    "vlan_name_id":[{"_action":"modify", "name": vlan_name,
                                     "vlan-ids": vlan_id.replace(" ", "")}]}
            result, changed = api.post(url=config_url, data=data)
            resp = result['resp']
        else:
            resp = []
            vlan_id_list = get_vlan_list(vlan_id)
            for vlan in vlan_id_list:
                data = {"id": vlan}
                result, changed = api.post(url=config_url, data=data)
                resp.append(result['resp'])

        module.exit_json(changed=changed, response=resp,
                               response_code=result['code'])

    elif action == "delete":
        if vlan_id and vlan_name:
            module.fail_json(change=False, response= result['resp'],
                             msg="To delete named VLAN, first delete a valid vlan_name."
                                 " Then use the vlan_id in a subsequent task if"
                                 " you wish to remove the VLAN ID associated to the"
                                 " named VLAN.")
        elif vlan_name and vlan_id is None:
            config_url = "/v1/configuration/object?config_path=" + str(config_path)
            data = {"vlan_name_id": [{"_action":"delete", "name": vlan_name}],
                    "vlan_name": [{"_action": "delete", "name": vlan_name}]}
            result, changed = api.post(url=config_url, data=data)
            resp = result['resp']
        else:
            vlan_id_list = get_vlan_list(vlan_id)
            resp = []
            for vlan in vlan_id_list:
                data = {"id": int(vlan), "_action": "delete"}
                result, changed = api.post(url=config_url, data=data)
                resp.append(result['resp'])
        module.exit_json(changed=changed, response=resp, response_code=result['code'])

    elif action == "get":
        if type_vlan == "named_vlan":
            config_url = "/v1/configuration/object/vlan_name_id?config_path="+str(config_path)
        result = api.get(url=config_url)
        resp = result['resp']
        if "_data" in resp.keys():
            module.exit_json(changed=False, response=resp, response_code=result['code'],
                             msg="Response shows the VLANs configured on the "
                                 "given config_path along with the ones inherited "
                                 "from the hierarchy above")
        else:
            module.fail_json(changed=False, response=result['resp'],
                             response_code=result['code'])

    else:
        module.fail_json(changed=False, response=result['resp'],
                         response_code=result['code'],
                         msg=str("Verify the playbook based on the playbook example"
                                 " in the module documentation."))


if __name__ == '__main__':
    main()
