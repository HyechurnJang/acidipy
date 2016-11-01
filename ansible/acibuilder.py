#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on 2016. 10. 11.

@author: "comfact"
'''

from ansible.module_utils.basic import *
from acidipy import deployACI

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
            description=dict(required=True)
        ),
        supports_check_mode = True
    )
    
    result = deployACI(module.params['description'])
    module.exit_json(**result)

main()