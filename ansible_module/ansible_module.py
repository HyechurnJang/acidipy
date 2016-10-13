#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on 2016. 10. 11.

@author: "comfact"
'''

from ansible.module_utils.basic import *
from acidipy import *

DOCUMENTATION = '''
---
module: hyping
version_added: historical
short_description: Try to connect to host and return C(pong) on success.
description:
   - A trivial test module, this module always returns C(pong) on successful
     contact. It does not make sense in playbooks, but it is useful from
     C(/usr/bin/ansible)
options: {}
author: Michael DeHaan
'''

EXAMPLES = '''
# Test 'webservers' status
ansible webservers -m ping
'''

def main():
    module = AnsibleModule(
        argument_spec = dict(
            data=dict(required=False, default=None),
        ),
        supports_check_mode = True
    )
    result = dict(ping='pong')
    if module.params['data']:
        result['ping'] = module.params['data']
    module.exit_json(**result)

main()