#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on 2016. 10. 11.

@author: "comfact"
'''

import yaml
from ansible.module_utils.basic import *
from acidipy import deployACI

DOCUMENTATION = '''
---
module: acibuilder
version_added: historical
short_description: acidipy ansible module.
description:
   - This is Acidipy Ansible Module named AciBuilder
options: {}
author: hyjang@cisco.com
'''

EXAMPLES = '''
# Test 'webservers' status
ansible webservers -m ping
'''

def main():

    module = AnsibleModule(
        argument_spec = dict(
            Controller=dict(required=True),
            Option=dict(required=True),
            Tenant=dict(required=True)
        ),
        supports_check_mode = True
    )
    
    ctrl = yaml.load(module.params['Controller'])
    opts = yaml.load(module.params['Option'])
    tnts = yaml.load(module.params['Tenant'])
    
    desc = {'Controller' : ctrl, 'Option' : opts, 'Tenant' : tnts}
    result = deployACI(desc)
    module.exit_json(**result)

main()
