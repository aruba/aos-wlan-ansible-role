
#!/usr/bin/python3
'''
#Aruba OS 8(AOS8) API module
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
module: aos_api_config
version_added: 2.8.1
short_descriptions: REST API module for ArubaOS 8.X
description: This module provides a configuration mechanism of ArubaOS products like Mobility Master and
                   Mobility Controllers using AOS 8 API
options:
    api_object:
        description:
            - Name of the API endpoint for which you would like to fetch data
              from the system. List of API endpoints can  be obtained at:
              https://<mm-ip-address>:4343/api (use your Mobility Master's IP)
        required: true
        type: str

    method:
        description:
            - HTTP Method to be used for the API call
        required: true
        choices:
            - GET
            - POST
        type: str

    config_path:
        description:
            - Path in the hierarchy where the API call should be applied
        required: false
        type: str

    data:
        description:
            - list of dictionaries where each element of list is a key value pairs
              of api object and corresponding configuration
        required: false
        type: list

    commit:
        description:
            - If set to True, it does a write_memory to flash
        required: false
        type: bool

    filter:
        description:
            - Filter applied on the data received by a GET request
              There are two types of filters:
              1) Object Filter:
                 An object filter limits which objects or which sub_objects should
                 be present in the response. Only one filter can be applied per request.
                 Object filter syntax is as follows:
                 [{"OBJECT" : { "<oper>" : [ <parameters> ] } } ]

                 <oper>
                   - $eq (matches one of the values)
                   - $neq (does not match any of the values)

                   <parameters> Comma separated values which need to be
                                filtered based on the operation

              2) Data Filter:
                 It filters out the configuration elements configured on the system.
                 Any filter which is not an object filter is a data filter.
                 Data filter should be applied as follows:
                 [{"<param-name" : { "<oper>" : <list-of-values> } } ]

                 <param_name> Fully qualified name of the parameter on values of
                               which filter needs to be applied

                  <oper>
                    - $eq (matches one of the values)
                    - $neq (does not match any of the values)
                    - $gt (matches a value which is greater than the filter)
                    - $gte (matches a value which is greater than or equal to the filter)
                    - $lt (matches a value which is less than the filter)
                    - $lte (matches a value which is less than or equal to the filter)
                    - $nin (pattern does not match the filter. Opposite of $in)
                    - $in (pattern matches the filter value. E.g., if filter says "ap",
                           "default-ap" and "ap-grp1" will both match)
        required: false
        type: list

    sort:
        description:
            - Data from the GET response can be sorted based on a single field
              Sort syntax is as follws:
              <oper><key>

               <oper> Order in which you want the values
                 - "+" (for ascending)(*default)
                 - "-" (for descending)

                <key> Key is the parameter name on which sort must be applied.
                      It is in the form:
                      <objectname>.<param_name>
                      or
                      <objectname>.<subobject_ name>.<param_name>

                ( Example: +int_vlan.id )
                ( Example: +int_vlan.int_vlan_mtu.value )
        required: false
        type: str

    count:
        description:
            - The count modifier just returns the total count of an object for
              multi-instance object or for multi-instance sub- object rather than
              the actual details of the objects. This is particularly useful when
              you want to get only the number of instances in an object rather than
              the object details.
              Usage example: count: int_vlan.int_vlan_ip_helper
        required: false
        type: str

    limit:
        description:
            - The maximum number if instances of an object that should be put in a
              single reques
        required: false
        type: int

    offset:
        description:
            - This conveys the number of the entries from which the response should
              start the next data set. For example, offset value of 21 means that
              out of all the instances of an object, give me data from 21st object.
              Currently, we support offset value to be multiples of the limit field
              below plus one. For example, if limit is 20, then offset can take values
              of 1, 21, 41, 61, 81 etc.
        required: false
        type: int

    total:
        description:
            - The total or maximum number of values that a response should contain
        required: false
        type: int

"""
EXAMPLES = """
#Usage Examples
    - name: Create a radius server
      aos_api_config:
        method: POST
        config_path: /md/Boston
        data:
         - rad_server: #POST request where a single endpoint is configured
             - rad_server_name: test-dot1x
               rad_host:
                 host: 1.1.1.1

       commit: True
        data: { "rad_server_name": "test_dot1x" ,"rad_host": {"host": "1.1.1.1"} }

    - name: Add a new VLAN, use it as an Interface VLAN and commit the pending changes
      aos_api_config:
        method: POST
        config_path: /md/SLR
        data:   #Multipart POST request where multiple endpoints are configured at once
         - vlan_id:
             - id: 45
         - int_vlan:
             - id: 45
               int_vlan_ip:
                 ipaddr: 1.1.1.45
                 ipmask: 255.0.0.0
       commit: True

    - name: GET the hostname of MM
      aos_api_config:
        method: GET
        api_object: hostname
        config_path: /mm/mynode

    - name: GET only profile names of SSIDs configured at /md/Boston
      aos_api_config:
        method: GET
        api_object: ssid_prof
        config_path: /md/Boston
        filter: [ {'OBJECT': { '$eq': [ 'ssid_prof.profile-name' ] } } ]




"""
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.aos_http import AosApi

def main():
    '''
    Module args and module logic
    '''
    module = AnsibleModule(
        argument_spec=dict(
            method=dict(required=True, type='str', choices=['GET', 'POST']),
            config_path=dict(required=True, type='str', default=None),
            data=dict(required=False, type='list', elements='dict', default=list()),
            commit=dict(required=False, type='bool', default=False),
            api_object=dict(required=False, type='str', default=None),
            #GET response modifiers
            filter=dict(required=False, type='list', default=list()),
            sort=dict(required=False, type='str', default=None),
            count=dict(required=False, type='str', default=None),
            limit=dict(required=False, type='int', default=None),
            offset=dict(required=False, type='int', default=None),
            total=dict(required=False, type='int', default=None),
            type=dict(required=False, type='str', default=None),

        ))

    config_path = module.params.get('config_path')
    method = module.params.get('method')
    api = AosApi(module)

    if method == "GET":
        api_object = module.params.get('api_object')
        query_url = '/configuration/object/' + api_object
        query_params = api.get_query_params()
        request = api.get_url(query_url, params=query_params)
        result = api.get(url=request)
        resp = result['resp']
        code = result['code']

        try:
            if "_data" in resp.keys():
                module.exit_json(changed=False, response=resp, response_code=code)
            elif resp is not None:
                module.exit_json(changed=False, response=resp, response_code=code)
            else:
                module.fail_json(change=False, response=resp, response_code=code,
                                 msg=str("Check if valid parameters are provided"
                                         " in the playbook."))
        except AttributeError:
            module.exit_json(changed=False, response=resp, response_code=code)

    if method == "POST":
        failed = False
        commit_status = False
        commit = module.params.get('commit')
        config_url = api.get_url('/configuration/object', params={'config_path': config_path})
        data = api.format_data()
        result, changed = api.post(url=config_url, data=data)
        resp = result['resp']
        code = result['code']
        if code == 200:
            if resp and resp != "":
                res, pending, status_str = api.validate_response(resp)
                failed = True if not res else False

                # write_memory if commit is true
                if commit and pending != 0:
                    commit_status = api.write_mem()
        else:
            failed = True

        if failed:
            module.fail_json(changed=changed, response=resp,
                             response_code=code, msg=status_str)
        else:
            module.exit_json(changed=changed, response=resp,
                             response_code=code, msg=status_str)
    else:
        module.fail_json(changed=False, msg="Invalid method type."
                         " Only GET and POST methods are supported on"
                         " Aruba Mobility Master and Controllers")

if __name__ == '__main__':
    main()
