'''
Created on 2016. 10. 6.

@author: "comfact"
'''

import json
from .base import ACIObject

class Tenant(ACIObject):
    _OBJECT = 'fvTenant'
    _IDENTY = '/tn-'
    _PRIKEY = 'name'
    _PKTMPL = '%s'
    _PARENT = 'Domain'
    _CHILD = [
              'fvAp',
              'fvBD',
              ]
    _RSOBJ = []
    _RTOBJ = []
    
    def __init__(self, name, **attributes):
        ACIObject.__init__(self, name=name, **attributes)

class AppProf(ACIObject):
    _OBJECT = 'fvAp'
    _IDENTY = '/ap-'
    _PRIKEY = 'name'
    _PKTMPL = '%s'
    _PARENT = 'fvTenant'
    _CHILD = [
              'fvAEPg',
              ]
    _RSOBJ = []
    _RTOBJ = []
    
    def __init__(self, name, **attributes):
        ACIObject.__init__(self, name=name, **attributes)
        
class BridgeDomain(ACIObject):
    _OBJECT = 'fvBD'
    _IDENTY = '/BD-'
    _PRIKEY = 'name'
    _PKTMPL = '%s'
    _PARENT = 'fvTenant'
    _CHILD = [
              'fvSubnet',
              ]
    _RSOBJ = []
    _RTOBJ = [
              'fvAEPg'
              ]
    
    def __init__(self, name, **attributes):
        ACIObject.__init__(self, name=name, **attributes)
        
class EndPointGroup(ACIObject):
    _OBJECT = 'fvAEPg'
    _IDENTY = '/epg-'
    _PRIKEY = 'name'
    _PKTMPL = '%s'
    _PARENT = 'fvAp'
    _CHILD = []
    _RSOBJ = [
              'fvBD'
              ]
    _RTOBJ = []
    
    def __init__(self, name, **attributes):
        ACIObject.__init__(self, name=name, **attributes)
        
    def relate(self, rel):
        if isinstance(rel, BridgeDomain):
            if self._domain.create(self['dn'], json.dumps({'fvRsBd' : {'attributes' : {'tnFvBDName' : rel['name']}}})):
                self.getRefresh()
                rel.getRefresh()
                return True
        return False

class Subnet(ACIObject):
    _OBJECT = 'fvSubnet'
    _IDENTY = '/subnet-'
    _PRIKEY = 'ip'
    _PKTMPL = '[%s]'
    _PARENT = 'fvBD'
    _CHILD = []
    _RSOBJ = []
    _RTOBJ = []
    
    def __init__(self, name, ip, **attributes):
        ACIObject.__init__(self, name=name, ip=ip, **attributes)






