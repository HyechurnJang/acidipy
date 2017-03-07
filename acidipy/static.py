'''
Created on 2016. 10. 24.

@author: "comfact"
'''

ACIDIPY_REFRESH_SEC = 180
ACIDIPY_SUBSCRIBER_REFRESH_SEC = 60

#===============================================================================
# Exception & Error
#===============================================================================

class ExceptAcidipySession(Exception):
    def __init__(self, session):
        Exception.__init__(self, '[Error]Acidipy:Session:%s' % session.url)
        if session.debug: print('[Error]Acidipy:Session:%s' % session.url)

class ExceptAcidipyResponse(Exception):
    def __init__(self, session, code, text):
        Exception.__init__(self, '[Error]Acidipy:Response:%s:%s' % (code, text))
        if session.debug: print('[Error]Acidipy:Response:%s:%s' % (code, text))
        
class ExceptAcidipySubscriberSession(Exception):
    def __init__(self, subscriber):
        Exception.__init__(self, '[Error]Acidipy:Subscriber:Session:wss://%s/socket%s' % (subscriber.controller.ip, subscriber.controller.cookie))
        if subscriber.controller.debug: print('[Error]Acidipy:Subscriber:Session:wss://%s/socket%s' % (subscriber.controller.ip, subscriber.controller.cookie))

class ExceptAcidipySubscriberRegister(Exception):
    def __init__(self, subscriber, exp=None):
        Exception.__init__(self, '[Error]Acidipy:Subscriber:Register:wss://%s/socket%s:%s' % (subscriber.controller.ip, subscriber.controller.cookie, str(exp)))
        if subscriber.controller.debug: print('[Error]Acidipy:Subscriber:Register:wss://%s/socket%s:%s' % (subscriber.controller.ip, subscriber.controller.cookie, str(exp)))

class ExceptAcidipyProcessing(Exception):
    def __init__(self, session, msg):
        Exception.__init__(self, '[Error]Acidipy:Processing:%s:' % msg)
        if session.debug: print('[Error]Acidipy:Processing:%s:' % msg)

class ExceptAcidipyAttributes(Exception):
    def __init__(self, session, target, exp):
        Exception.__init__(self, '[Error]Acidipy:Attributes:%s:%s' % (target, str(exp)))
        if session.debug: print('[Error]Acidipy:Attributes:%s:%s' % (target, str(exp)))

class ExceptAcidipyRetriveObject(Exception):
    def __init__(self, session, target, exp):
        Exception.__init__(self, '[Error]Acidipy:RetriveObject:%s:%s' % (target, str(exp)))
        if session.debug: print('[Error]Acidipy:RetriveObject:%s:%s' % (target, str(exp)))

class ExceptAcidipyCreateObject(Exception):
    def __init__(self, session, target, exp):
        Exception.__init__(self, '[Error]Acidipy:CreateObject:%s:%s' % (target, str(exp)))
        if session.debug: print('[Error]Acidipy:CreateObject:%s:%s' % (target, str(exp)))

class ExceptAcidipyUpdateObject(Exception):
    def __init__(self, session, target, exp):
        Exception.__init__(self, '[Error]Acidipy:UpdateObject:%s:%s' % (target, str(exp)))
        if session.debug: print('[Error]Acidipy:UpdateObject:%s:%s' % (target, str(exp)))

class ExceptAcidipyDeleteObject(Exception):
    def __init__(self, session, target, exp):
        Exception.__init__(self, '[Error]Acidipy:DeleteObject:%s:%s' % (target, str(exp)))
        if session.debug: print('[Error]Acidipy:DeleteObject:%s:%s' % (target, str(exp)))

class ExceptAcidipyRelateObject(Exception):
    def __init__(self, session, target, exp):
        Exception.__init__(self, '[Error]Acidipy:RelateObject:%s:%s' % (target, str(exp)))
        if session.debug: print('[Error]Acidipy:RelateObject:%s:%s' % (target, str(exp)))

class ExceptAcidipyNonExistData(Exception):
    def __init__(self, session, target):
        Exception.__init__(self, '[Error]Acidipy:NonExistData:%s' % target)
        if session.debug: print('[Error]Acidipy:NonExistData:%s' % target)

class ExceptAcidipyNonExistCount(Exception):
    def __init__(self, session, target):
        Exception.__init__(self, '[Error]Acidipy:NonExistCount:%s' % target)
        if session.debug: print('[Error]Acidipy:NonExistCount:%s' % target)

class ExceptAcidipyNonExistParent(Exception):
    def __init__(self, session, target):
        Exception.__init__(self, '[Error]Acidipy:NonExistParent:%s' % target)
        if session.debug: print('[Error]Acidipy:NonExistParent:%s' % target)

class ExceptAcidipyNonExistHealth(Exception):
    def __init__(self, session, target):
        Exception.__init__(self, '[Error]Acidipy:NonExistHealth:%s' % target)
        if session.debug: print('[Error]Acidipy:NonExistHealth:%s' % target)

#===============================================================================
# Prepare Classes
#===============================================================================
PREPARE_CLASSES = {
    'fvTenant' :             'TenantObject',
    'vzFilter' :             'FilterObject',
    'vzBrCP' :               'ContractObject',
    'fvCtx' :                'ContextObject',
    'l3extOut' :             'L3OutObject',
    'l3extInstP' :           'L3ProfileObject',
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