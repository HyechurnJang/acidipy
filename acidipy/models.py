'''
Created on 2016. 10. 6.

@author: "comfact"
'''

from .base import ACIObject

class Tenant(ACIObject):
    _OBJECT = 'fvTenant'
    _IDENTY = '/tn-'
    _PARENT = None
    
    def __init__(self, name, **attributes):
        ACIObject.__init__(self, name=name, **attributes)
        
class BridgeDomain(ACIObject):
    _OBJECT = 'fvBD'
    _IDENTY = '/BD-'
    _PARENT = 'fvTenant'
    
    def __init__(self, name, **attributes):
        ACIObject.__init__(self, name=name, **attributes)
        
class AppProf(ACIObject):
    _OBJECT = 'fvAp'
    _IDENTY = '/ap-'
    _PARENT = 'fvTenant'
    
    def __init__(self, name, **attributes):
        ACIObject.__init__(self, name=name, **attributes)
        
class EndPointGroup(ACIObject):
    _OBJECT = 'fvAEPg'
    _IDENTY = '/epg-'
    _PARENT = 'fvAp'
    
    def __init__(self, name, **attributes):
        ACIObject.__init__(self, name=name, **attributes)
        
    def setBridgeDomain(self, bd):
        if not isinstance(bd, BridgeDomain): return False
        self['scope'] = bd.getDetail()['scope']
        return self.update()
