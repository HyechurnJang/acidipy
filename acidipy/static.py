'''
Created on 2016. 10. 24.

@author: "comfact"
'''

#===============================================================================
# Default Settings
#===============================================================================
ACIDIPY_REFRESH_SEC = 180
ACIDIPY_SUBSCRIBER_REFRESH_SEC = 60

#===============================================================================
# Prepare Classes
#===============================================================================
PREPARE_CLASSES = {
    'fvTenant' :             'AciTenant',
    'vzFilter' :             'AciFilter',
    'vzBrCP' :               'AciContract',
    'fvCtx' :                'AciContext',
    'l3extOut' :             'AciL3Out',
    'l3extInstP' :           'AciL3Profile',
    'fvBD' :                 'AciBridgeDomain',
    'fvAp' :                 'AciAppProfile',
    'vzEntry' :              'AciFilterEntry',
    'vzSubj' :               'AciSubject',
    'fvSubnet' :             'AciSubnet',
    'fvAEPg' :               'AciEPG',
    'fvCEp' :                'AciEndpoint',
    'fabricPod' :            'AciPod',
    'fabricNode' :           'AciNode',
    'fabricPathEpCont' :     'AciPaths',
    'fabricProtPathEpCont' : 'AciVPaths',
    'fabricPathEp' :         'AciPath',
    'topSystem' :            'AciSystem',
    'l1PhysIf' :             'AciPhysIf',
}

PREPARE_ATTRIBUTES = {
}

#===============================================================================
# Exception & Error
#===============================================================================

class ExceptAcidipyAbstract(Exception):
    def __init__(self, session, msg):
        Exception.__init__(self, msg)
        if session.debug: print msg

class ExceptAcidipySession(ExceptAcidipyAbstract):
    def __init__(self, session):
        ExceptAcidipyAbstract.__init__(self, session, '[Error]Acidipy:Session:%s' % session.url)

class ExceptAcidipyResponse(ExceptAcidipyAbstract):
    def __init__(self, session, code, text):
        ExceptAcidipyAbstract.__init__(self, session, '[Error]Acidipy:Response:%s:%s' % (code, text))
        
class ExceptAcidipyEventTriggerSession(ExceptAcidipyAbstract):
    def __init__(self, subscriber):
        ExceptAcidipyAbstract.__init__(self, subscriber.controller, '[Error]Acidipy:EventTrigger:Session:wss://%s/socket%s' % (subscriber.controller.ip, subscriber.controller.cookie))

class ExceptAcidipyEventTriggerRegister(ExceptAcidipyAbstract):
    def __init__(self, subscriber, exp=None):
        ExceptAcidipyAbstract.__init__(self, subscriber.controller, '[Error]Acidipy:EventTrigger:Register:wss://%s/socket%s>>%s' % (subscriber.controller.ip, subscriber.controller.cookie, str(exp)))

class ExceptAcidipyProcessing(ExceptAcidipyAbstract):
    def __init__(self, session, msg):
        ExceptAcidipyAbstract.__init__(self, session, '[Error]Acidipy:Processing:%s:' % msg)

class ExceptAcidipyAttributes(ExceptAcidipyAbstract):
    def __init__(self, session, target, exp):
        ExceptAcidipyAbstract.__init__(self, session, '[Error]Acidipy:Attributes:%s>>%s' % (target, str(exp)))

class ExceptAcidipyRetriveObject(ExceptAcidipyAbstract):
    def __init__(self, session, target, exp):
        ExceptAcidipyAbstract.__init__(self, session, '[Error]Acidipy:RetriveObject:%s>>%s' % (target, str(exp)))

class ExceptAcidipyCreateObject(ExceptAcidipyAbstract):
    def __init__(self, session, target, exp):
        ExceptAcidipyAbstract.__init__(self, session, '[Error]Acidipy:CreateObject:%s>>%s' % (target, str(exp)))

class ExceptAcidipyUpdateObject(ExceptAcidipyAbstract):
    def __init__(self, session, target, exp):
        ExceptAcidipyAbstract.__init__(self, session, '[Error]Acidipy:UpdateObject:%s>>%s' % (target, str(exp)))

class ExceptAcidipyDeleteObject(ExceptAcidipyAbstract):
    def __init__(self, session, target, exp):
        ExceptAcidipyAbstract.__init__(self, session, '[Error]Acidipy:DeleteObject:%s>>%s' % (target, str(exp)))

class ExceptAcidipyRelateObject(ExceptAcidipyAbstract):
    def __init__(self, session, target, exp):
        ExceptAcidipyAbstract.__init__(self, session, '[Error]Acidipy:RelateObject:%s>>%s' % (target, str(exp)))

class ExceptAcidipyNonExistData(ExceptAcidipyAbstract):
    def __init__(self, session, target):
        ExceptAcidipyAbstract.__init__(self, session, '[Error]Acidipy:NonExistData:%s' % target)

class ExceptAcidipyNonExistCount(ExceptAcidipyAbstract):
    def __init__(self, session, target):
        ExceptAcidipyAbstract.__init__(self, session, '[Error]Acidipy:NonExistCount:%s' % target)

class ExceptAcidipyNonExistParent(ExceptAcidipyAbstract):
    def __init__(self, session, target):
        ExceptAcidipyAbstract.__init__(self, session, '[Error]Acidipy:NonExistParent:%s' % target)

class ExceptAcidipyNonExistHealth(ExceptAcidipyAbstract):
    def __init__(self, session, target):
        ExceptAcidipyAbstract.__init__(self, session, '[Error]Acidipy:NonExistHealth:%s' % target)
