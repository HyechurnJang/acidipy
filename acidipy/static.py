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
    'fvTenant' :             'aciTenantModel',
    'vzFilter' :             'aciFilterModel',
    'vzBrCP' :               'aciContractModel',
    'fvCtx' :                'aciContextModel',
    'l3extOut' :             'aciL3OutModel',
    'l3extInstP' :           'aciL3ProfileModel',
    'fvBD' :                 'aciBridgeDomainModel',
    'fvAp' :                 'aciAppProfileModel',
    'vzEntry' :              'aciFilterEntryModel',
    'vzSubj' :               'aciSubjectModel',
    'fvSubnet' :             'aciSubnetModel',
    'fvAEPg' :               'aciEPGModel',
    'fvCEp' :                'aciEndpointModel',
    'fabricPod' :            'aciPodModel',
    'fabricNode' :           'aciNodeModel',
    'fabricPathEpCont' :     'aciPathsModel',
    'fabricProtPathEpCont' : 'aciVPathsModel',
    'fabricPathEp' :         'aciPathModel',
    'topSystem' :            'aciSystemModel',
    'l1PhysIf' :             'aciPhysIfModel',
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
        
class ExceptAcidipySubscriberSession(ExceptAcidipyAbstract):
    def __init__(self, subscriber):
        ExceptAcidipyAbstract.__init__(self, subscriber.controller, '[Error]Acidipy:Subscriber:Session:wss://%s/socket%s' % (subscriber.controller.ip, subscriber.controller.cookie))

class ExceptAcidipySubscriberRegister(ExceptAcidipyAbstract):
    def __init__(self, subscriber, exp=None):
        ExceptAcidipyAbstract.__init__(self, subscriber.controller, '[Error]Acidipy:Subscriber:Register:wss://%s/socket%s:%s' % (subscriber.controller.ip, subscriber.controller.cookie, str(exp)))

class ExceptAcidipyProcessing(ExceptAcidipyAbstract):
    def __init__(self, session, msg):
        ExceptAcidipyAbstract.__init__(self, session, '[Error]Acidipy:Processing:%s:' % msg)

class ExceptAcidipyAttributes(ExceptAcidipyAbstract):
    def __init__(self, session, target, exp):
        ExceptAcidipyAbstract.__init__(self, session, '[Error]Acidipy:Attributes:%s:%s' % (target, str(exp)))

class ExceptAcidipyRetriveObject(ExceptAcidipyAbstract):
    def __init__(self, session, target, exp):
        ExceptAcidipyAbstract.__init__(self, session, '[Error]Acidipy:RetriveObject:%s:%s' % (target, str(exp)))

class ExceptAcidipyCreateObject(ExceptAcidipyAbstract):
    def __init__(self, session, target, exp):
        ExceptAcidipyAbstract.__init__(self, session, '[Error]Acidipy:CreateObject:%s:%s' % (target, str(exp)))

class ExceptAcidipyUpdateObject(ExceptAcidipyAbstract):
    def __init__(self, session, target, exp):
        ExceptAcidipyAbstract.__init__(self, session, '[Error]Acidipy:UpdateObject:%s:%s' % (target, str(exp)))

class ExceptAcidipyDeleteObject(ExceptAcidipyAbstract):
    def __init__(self, session, target, exp):
        ExceptAcidipyAbstract.__init__(self, session, '[Error]Acidipy:DeleteObject:%s:%s' % (target, str(exp)))

class ExceptAcidipyRelateObject(ExceptAcidipyAbstract):
    def __init__(self, session, target, exp):
        ExceptAcidipyAbstract.__init__(self, session, '[Error]Acidipy:RelateObject:%s:%s' % (target, str(exp)))

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
