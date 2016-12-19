'''
Created on 2016. 10. 24.

@author: "comfact"
'''

#===============================================================================
# Exception & Error
#===============================================================================

class AcidipyError(Exception):
    def __init__(self, code, text):
        self.code = code
        self.text = text
    def __str__(self): return 'code:%s-text:%s' % (self.code, self.text)

class AcidipySessionError(Exception): 
    def __str__(self): return 'Acidipy Session Error'

class AcidipySubscriptionError(Exception): pass

class AcidipyAttributesError(Exception): pass

class AcidipyNonExistData(Exception):
    def __init__(self, target_name): self.target_name = target_name
    def __str__(self): return 'Non exist data of %s' % self.target_name
    
class AcidipyNonExistParent(Exception):
    def __init__(self, target_name): self.target_name = target_name
    def __str__(self): return 'Non exist parent of %s' % self.target_name
    
class AcidipyNonExistChildren(Exception):
    def __init__(self, target_name): self.target_name = target_name
    def __str__(self): return 'Non exist children of %s' % self.target_name
    
class AcidipyNonExistHealth(Exception):
    def __init__(self, target_name): self.target_name = target_name
    def __str__(self): return 'Non exist health of %s' % self.target_name
    
class AcidipyNonExistCount(Exception):
    def __init__(self, target_name): self.target_name = target_name
    def __str__(self): return 'Non exist count of %s' % self.target_name
    
class AcidipyCreateError(Exception):
    def __init__(self, target_name): self.target_name = target_name
    def __str__(self): return 'Create failed with %s' % self.target_name
    
class AcidipyUpdateError(Exception):
    def __init__(self, target_name): self.target_name = target_name
    def __str__(self): return 'Update failed with %s' % self.target_name
    
class AcidipyDeleteError(Exception):
    def __init__(self, target_name): self.target_name = target_name
    def __str__(self): return 'Delete failed with %s' % self.target_name
    
class AcidipyRelateError(Exception):
    def __init__(self, target_name): self.target_name = target_name
    def __str__(self): return 'Relate failed with %s' % self.target_name

#===============================================================================
# Prepare Classes
#===============================================================================
PREPARE_CLASSES = {
    'fvTenant' :             'TenantObject',
    'vzFilter' :             'FilterObject',
    'vzBrCP' :               'ContractObject',
    'fvCtx' :                'ContextObject',
    'l3extOut' :             'L3ExternalObject',
    'fvBD' :                 'BridgeDomainObject',
    'fvAp' :                 'AppProfileObject',
    'vzEntry' :              'FilterEntryObject',
    'vzSubj' :               'SubjectObject',
    'fvSubnet' :             'SubnetObject',
    'fvAEPg' :               'EPGObject',
    'fvCEp' :                'EndpointObject',
    'fabricPod' :            'PodObject',
    'fabricNode' :           'NodeObject',
    'fabricPathEpCont' :     'PathsObject',
    'fabricProtPathEpCont' : 'VPathsObject',
    'fabricPathEp' :         'PathObject',
    'topSystem' :            'SystemObject',
    'l1PhysIf' :             'PhysIfObject',
}

PREPARE_ATTRIBUTES = {
}