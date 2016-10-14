'''
Created on 2016. 10. 11.

@author: "comfact"
'''

import json

from .modelbase import ACIObject

class Pod(ACIObject):
    _OBJECT = 'fabricPod'
    _IDENTY = '/pod-'
    _PRIKEY = 'id'
    _PKTMPL = '%s'
    
    _PARENT = 'Domain'
    _CHILD = [
              'fabricNode',
              ]
    _RELAT = []
    
    _HEALTH_TYPE = ACIObject.HEALTH_TYPE_URL
    _HEALTH_URL = '/api/node/class/fabricHealthTotal.json?query-target-filter=and(wcard(fabricHealthTotal.dn,"pod-.*/health"))'
    _HEALTH_KEY = 'cur'
    @classmethod
    def _HEALTH_DNF(cls, dn): return dn.split('/health')[0]
    
    def __init__(self, name, **attributes):
        ACIObject.__init__(self, name=name, **attributes)
    

class Node(ACIObject):
    _OBJECT = 'fabricNode'
    _IDENTY = '/node-'
    _PRIKEY = 'id'
    _PKTMPL = '%s'
    
    _PARENT = 'fabricPod'
    _CHILD = []
    _RELAT = []
    
    _HEALTH_TYPE = ACIObject.HEALTH_TYPE_URL
    _HEALTH_URL = '/api/node/class/fabricNodeHealth5min.json'
    _HEALTH_KEY = 'healthLast'
    @classmethod
    def _HEALTH_DNF(cls, dn): return dn.split('/sys/CD')[0]
    
    def __init__(self, name, **attributes):
        ACIObject.__init__(self, name=name, **attributes)

