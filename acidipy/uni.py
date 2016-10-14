'''
Created on 2016. 10. 6.

@author: "comfact"
'''

import json

from .modelbase import ACIObject

class Tenant(ACIObject):
    _OBJECT = 'fvTenant'
    _IDENTY = '/tn-'
    _PRIKEY = 'name'
    _PKTMPL = '%s'
    
    _PARENT = 'Domain'
    _CHILD = [
              'fvAp',
              'fvBD',
              'fvCtx',
              ]
    _RELAT = []
    
    _HEALTH_TYPE = ACIObject.HEALTH_TYPE_CHILD
    
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
    _RELAT = []
    
    _HEALTH_TYPE = ACIObject.HEALTH_TYPE_CHILD
    
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
    _RELAT = [
              'fvCtx'
              ]
    
    _HEALTH_TYPE = ACIObject.HEALTH_TYPE_CHILD
    
    def __init__(self, name, **attributes):
        ACIObject.__init__(self, name=name, **attributes)
        
    def relate(self, rel):
        if isinstance(rel, Context):
            if self._domain.create(self['dn'], json.dumps({'fvRsCtx' : {'attributes' : {'tnFvCtxName' : rel['name']}}})):
                self.getRefresh()
                rel.getRefresh()
                return True
        return False
        
class Context(ACIObject):
    _OBJECT = 'fvCtx'
    _IDENTY = '/ctx-'
    _PRIKEY = 'name'
    _PKTMPL = '%s'
    
    _PARENT = 'fvTenant'
    _CHILD = []
    _RELAT = []
    
    _HEALTH_TYPE = ACIObject.HEALTH_TYPE_CHILD
    
    def __init__(self, name, **attributes):
        ACIObject.__init__(self, name=name, **attributes)
        
class EndPointGroup(ACIObject):
    _OBJECT = 'fvAEPg'
    _IDENTY = '/epg-'
    _PRIKEY = 'name'
    _PKTMPL = '%s'
    
    _PARENT = 'fvAp'
    _CHILD = []
    _RELAT = [
              'fvBD'
              ]
    
    _HEALTH_TYPE = ACIObject.HEALTH_TYPE_CHILD
    
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
    _RELAT = []
    
    _HEALTH_TYPE = ACIObject.HEALTH_TYPE_NONE
    
    def __init__(self, ip, name=None, **attributes):
        if name != None: ACIObject.__init__(self, ip=ip, name=name, **attributes)
        else: ACIObject.__init__(self, ip=ip, **attributes)
