'''
Created on 2016. 10. 18.

@author: "comfact"
'''

import re
import ssl
import json

from websocket import create_connection
from pygics import Thread, Task, Scheduler

# GEVENT
import gevent.monkey
gevent.monkey.patch_socket()
gevent.monkey.patch_ssl()
import gevent

from .static import *
from .session import Session

class SubscribeHandler:
    def subscribe(self, status, obj): pass

###############################################################
#  ________  ________ _________  ________  ________     
# |\   __  \|\   ____\\___   ___\\   __  \|\   __  \    
# \ \  \|\  \ \  \___\|___ \  \_\ \  \|\  \ \  \|\  \   
#  \ \   __  \ \  \       \ \  \ \ \  \\\  \ \   _  _\  
#   \ \  \ \  \ \  \____   \ \  \ \ \  \\\  \ \  \\  \| 
#    \ \__\ \__\ \_______\  \ \__\ \ \_______\ \__\\ _\ 
#     \|__|\|__|\|_______|   \|__|  \|_______|\|__|\|__|
#                                                       
###############################################################

class AcidipyActor:
    
    def __init__(self, parent, class_name, class_pkey=None, class_ident=None):
        self.parent = parent
        self.controller = parent.controller
        self.class_name = class_name
        self.class_pkey = class_pkey
        self.class_ident = class_ident
        if class_name in PREPARE_CLASSES: self.prepare_class = globals()[PREPARE_CLASSES[class_name]]
        else: self.prepare_class = None
    
    def keys(self):
        if self.class_name in PREPARE_ATTRIBUTES: return PREPARE_ATTRIBUTES[self.class_name]
        url = '/api/class/' + self.class_name + '.json?page=0&page-size=1'
        data = self.controller.get(url)
        try: keys = sorted(data[0][self.class_name]['attributes'].keys())
        except: raise AcidipyAttributesError()
        if 'childAction' in keys: keys.remove('childAction')
        if 'dn' in keys: keys.remove('dn'); keys.insert(0, 'dn')
        if 'name' in keys: keys.remove('name'); keys.insert(0, 'name')
        if 'id' in keys: keys.remove('id'); keys.insert(0, 'id')
        PREPARE_ATTRIBUTES[self.class_name] = keys
        return keys

    def list(self, detail=False, sort=None, page=None, **clause):
        url = '/api/mo/' + self.parent['dn'] + '.json?query-target=subtree&target-subtree-class=' + self.class_name
        if not detail: url += '&rsp-prop-include=naming-only'
        if len(clause) > 0:
            url += '&query-target-filter=and('
            for key in clause: url += 'eq(%s.%s,"%s"),' % (self.class_name, key, clause[key])
            url += ')'
        if sort != None:
            url += '&order-by='
            if isinstance(sort, list):
                for s in sort: url += self.class_name + ('.%s,' % s)
            else: url += self.class_name + ('.%s' % sort)
        if page != None:
            url += '&page=%d&page-size=%d' % (page[0], page[1])
        data = self.controller.get(url)
        ret = []
        for d in data:
            for class_name in d:
                acidipy_obj = AcidipyObject(**d[class_name]['attributes'])
                acidipy_obj.class_name = class_name
                acidipy_obj.controller = self.controller
                acidipy_obj.is_detail = detail
                if self.prepare_class:
                    acidipy_obj.__class__ = self.prepare_class
                    acidipy_obj.__patch__()
                ret.append(acidipy_obj)
        return ret
    
    def __call__(self, rn, detail=False):
        url = '/api/mo/' + self.parent['dn'] + (self.class_ident % rn) + '.json'
        if not detail: url += '?rsp-prop-include=naming-only'
        data = self.controller.get(url)
        for d in data:
            for class_name in d:
                acidipy_obj = AcidipyObject(**d[class_name]['attributes'])
                acidipy_obj.controller = self.controller
                acidipy_obj.class_name = class_name
                acidipy_obj.is_detail = detail
                if self.prepare_class:
                    acidipy_obj.__class__ = self.prepare_class
                    acidipy_obj.__patch__()
                return acidipy_obj
        raise AcidipyNonExistData(self.parent['dn'] + (self.class_ident % rn))
    
    def count(self, **clause):
        url = '/api/node/class/' + self.class_name + '.json?query-target-filter=and(wcard(' + self.class_name + '.dn,"' + self.parent['dn'] + '/.*"),'
#         url = '/api/node/class/' + self.class_name + '.json?' # query-target-filter=wcard(' + self.class_name + '.dn,"' + self.parent['dn'] + '/.*")&rsp-subtree-include=count'
        if len(clause) > 0:
            for key in clause: url += 'eq(%s.%s,"%s"),' % (self.class_name, key, clause[key])
        url += ')&rsp-subtree-include=count'
        data = self.controller.get(url)
        try: return int(data[0]['moCount']['attributes']['count'])
        except: raise AcidipyNonExistCount(self.class_name)
    
    def subscribe(self, handler):
        handler.class_name = self.class_name
        self.controller.subscriber.register(handler)
        
    def create(self, **attributes):
        if self.class_pkey == None or self.class_ident == None: raise AcidipyCreateError(self.class_name)
        acidipy_obj = AcidipyObject(**attributes)
        acidipy_obj.class_name = self.class_name
        if self.controller.post('/api/mo/' + self.parent['dn'] + '.json', acidipy_obj.toJson()):
            acidipy_obj.controller = self.controller
            acidipy_obj['dn'] = self.parent['dn'] + (self.class_ident % attributes[self.class_pkey])
            acidipy_obj.is_detail = False
            if self.prepare_class:
                acidipy_obj.__class__ = self.prepare_class
                acidipy_obj.__patch__()
            return acidipy_obj
        raise AcidipyCreateError(self.class_name)

class AcidipyActorHealth:

    def health(self):
        url = '/api/node/class/' + self.class_name + '.json?query-target-filter=wcard(' + self.class_name + '.dn,"' + self.parent['dn'] + '/.*")&rsp-subtree-include=health'
        data = self.controller.get(url)
        ret = []
        for d in data:
            for class_name in d:
                try: hinst = d[class_name]['children'][0]['healthInst']
                except: continue
                attrs = d[class_name]['attributes']
                obj = {'dn' : attrs['dn'], 'name' : attrs['name'], 'score' : int(hinst['attributes']['cur'])}
                ret.append(obj)
        return ret
    
class TenantActor(AcidipyActor, AcidipyActorHealth):
    def __init__(self, parent): AcidipyActor.__init__(self, parent, 'fvTenant', 'name', '/tn-%s')
    
class FilterActor(AcidipyActor):
    def __init__(self, parent): AcidipyActor.__init__(self, parent, 'vzFilter', 'name', '/flt-%s')

class ContractActor(AcidipyActor):
    def __init__(self, parent): AcidipyActor.__init__(self, parent, 'vzBrCP', 'name', '/brc-%s')

class ContextActor(AcidipyActor, AcidipyActorHealth):
    def __init__(self, parent): AcidipyActor.__init__(self, parent, 'fvCtx', 'name', '/ctx-%s')
    
class L3OutActor(AcidipyActor):
    def __init__(self, parent): AcidipyActor.__init__(self, parent, 'l3extOut', 'name', '/out-%s')

class L3ProfileActor(AcidipyActor):
    def __init__(self, parent): AcidipyActor.__init__(self, parent, 'l3extInstP', 'name', '/instP-%s')
    
class BridgeDomainActor(AcidipyActor, AcidipyActorHealth):
    def __init__(self, parent): AcidipyActor.__init__(self, parent, 'fvBD', 'name', '/BD-%s')

class AppProfileActor(AcidipyActor, AcidipyActorHealth):
    def __init__(self, parent): AcidipyActor.__init__(self, parent, 'fvAp', 'name', '/ap-%s')

class FilterEntryActor(AcidipyActor):
    def __init__(self, parent): AcidipyActor.__init__(self, parent, 'vzEntry', 'name', '/e-%s')

class SubjectActor(AcidipyActor):
    def __init__(self, parent): AcidipyActor.__init__(self, parent, 'vzSubj', 'name', '/subj-%s')

class SubnetActor(AcidipyActor):
    def __init__(self, parent): AcidipyActor.__init__(self, parent, 'fvSubnet', 'ip', '/subnet-[%s]')

class EPGActor(AcidipyActor, AcidipyActorHealth):
    def __init__(self, parent): AcidipyActor.__init__(self, parent, 'fvAEPg', 'name', '/epg-%s')

class EndpointActor(AcidipyActor):
    def __init__(self, parent): AcidipyActor.__init__(self, parent, 'fvCEp', 'name', '/cep-%s')

class PodActor(AcidipyActor):
    def __init__(self, parent): AcidipyActor.__init__(self, parent, 'fabricPod', 'id', '/pod-%s')
    def health(self):
        url = '/api/node/class/fabricHealthTotal.json?query-target-filter=ne(fabricHealthTotal.dn,"topology/health")'
        data = self.controller.get(url)
        ret = []
        for d in data:
            for class_name in d:
                attrs = d[class_name]['attributes']
                if self.parent['dn'] in attrs['dn']:
                    obj = {'dn' : attrs['dn'].replace('/health', ''), 'name' : attrs['dn'].split('/')[1].replace('pod-', ''), 'score' : int(attrs['cur'])}
                    ret.append(obj)
        return ret

class NodeActor(AcidipyActor):
    def __init__(self, parent): AcidipyActor.__init__(self, parent, 'fabricNode', 'id', '/node-%s')
    def health(self):
        url = '/api/node/class/healthInst.json?query-target-filter=wcard(healthInst.dn,"^sys/health")'
        data = self.controller.get(url)
        ret = []
        for d in data:
            for class_name in d:
                attrs = d[class_name]['attributes']
                if self.parent['dn'] in attrs['dn']:
                    obj = {'dn' : attrs['dn'].replace('/sys/health', ''), 'name' : attrs['dn'].split('/')[2].replace('node-', ''), 'score' : int(attrs['cur'])}
                    ret.append(obj)
        return ret
    
class PathsActor(AcidipyActor):
    def __init__(self, parent): AcidipyActor.__init__(self, parent, 'fabricPathEpCont', 'nodeId', '/paths-%s')

class VPathsActor(AcidipyActor):
    def __init__(self, parent): AcidipyActor.__init__(self, parent, 'fabricProtPathEpCont', 'nodeId', '/protpaths-%s')

class PathActor(AcidipyActor):
    def __init__(self, parent): AcidipyActor.__init__(self, parent, 'fabricPathEp', 'name', '/pathep-[%s]')
    
class PhysIfActor(AcidipyActor):
    def __init__(self, parent): AcidipyActor.__init__(self, parent, 'l1PhysIf', 'id', '/phys-[%s]')
    def health(self):
        url = '/api/node/class/healthInst.json?query-target-filter=wcard(healthInst.dn,"phys/health")'
        data = self.controller.get(url)
        ret = []
        for d in data:
            for class_name in d:
                attrs = d[class_name]['attributes']
                if self.parent['dn'] in attrs['dn']:
                    obj = {'dn' : attrs['dn'].replace('/phys/health', ''), 'name' : attrs['dn'].split('[')[1].replace(']/phys/health', ''), 'score' : int(attrs['cur'])}
                    ret.append(obj)
        return ret

########################################################################################
#  ________  ________  ________  _________  ________  ________  ________ _________   
# |\   __  \|\   __  \|\   ____\|\___   ___\\   __  \|\   __  \|\   ____\\___   ___\ 
# \ \  \|\  \ \  \|\ /\ \  \___|\|___ \  \_\ \  \|\  \ \  \|\  \ \  \___\|___ \  \_| 
#  \ \   __  \ \   __  \ \_____  \   \ \  \ \ \   _  _\ \   __  \ \  \       \ \  \  
#   \ \  \ \  \ \  \|\  \|____|\  \   \ \  \ \ \  \\  \\ \  \ \  \ \  \____   \ \  \ 
#    \ \__\ \__\ \_______\____\_\  \   \ \__\ \ \__\\ _\\ \__\ \__\ \_______\  \ \__\
#     \|__|\|__|\|_______|\_________\   \|__|  \|__|\|__|\|__|\|__|\|_______|   \|__|
#                        \|_________|                                                
#
########################################################################################

class AcidipyObject(dict):
    
    def __init__(self, **attributes):
        dict.__init__(self, **attributes)
    
    def __patch__(self):
        pass
    
    def toJson(self):
        data = {}
        data[self.class_name] = {'attributes' : self}
        return json.dumps(data, sort_keys=True)
    
    def keys(self):
        if self.class_name in PREPARE_ATTRIBUTES: return PREPARE_ATTRIBUTES[self.class_name]
        url = '/api/class/' + self.class_name + '.json?page=0&page-size=1'
        data = self.controller.get(url)
        try: keys = sorted(data[0][self.class_name]['attributes'].keys())
        except: raise AcidipyAttributesError()
        if 'childAction' in keys: keys.remove('childAction')
        if 'dn' in keys: keys.remove('dn'); keys.insert(0, 'dn')
        if 'name' in keys: keys.remove('name'); keys.insert(0, 'name')
        if 'id' in keys: keys.remove('id'); keys.insert(0, 'id')
        PREPARE_ATTRIBUTES[self.class_name] = keys
        return keys
    
    def dn(self):
        return self['dn']
    
    def rn(self):
        dn = self['dn']
        ret = re.match('(?P<path>.*)/(?P<key>\w+)-(?P<rn>\[?[\W\w]+\]?)$', dn)
        if ret: return ret.group('path'), ret.group('key'), ret.group('rn')
        ret = re.match('^(?P<rn>\w+)$', dn)
        if ret: return None, None, ret.group('rn')
        return None, None, None
    
    def path(self):
        return re.sub('/\w+-', '/', self['dn'])
    
    def detail(self):
        if not self.is_detail:
            url = '/api/mo/' + self['dn'] + '.json'
            data = self.controller.get(url)
            for d in data:
                for class_name in d:
                    attrs = d[class_name]['attributes']
                    for key in attrs: self[key] = attrs[key]
            self.is_detail = True
        return self

    def parent(self, detail=False):
        try: parent_dn = self['dn'].split(re.match('[\W\w]+(?P<rn>/\w+-\[?[\W\w]+]?)$', self['dn']).group('rn'))[0]
        except: raise AcidipyNonExistParent(self['dn'])
        url = '/api/mo/' + parent_dn + '.json'
        if not detail: url += '?rsp-prop-include=naming-only'
        data = self.controller.get(url)
        for d in data:
            for class_name in d:
                acidipy_obj = AcidipyObject(**d[class_name]['attributes'])
                acidipy_obj.controller = self.controller
                acidipy_obj.class_name = class_name
                acidipy_obj.is_detail = detail
                if class_name in PREPARE_CLASSES:
                    acidipy_obj.__class__ = globals()[PREPARE_CLASSES[class_name]]
                    acidipy_obj.__patch__()
                return acidipy_obj
        raise AcidipyNonExistData(parent_dn)

    def children(self, detail=False, sort=None, page=None, **clause):
        url = '/api/mo/' + self['dn'] + '.json?query-target=children'
        if not detail: url += '&rsp-prop-include=naming-only'
        if len(clause) > 0:
            url += '&query-target-filter=and('
            for key in clause: url += 'eq(%s.%s,"%s"),' % (self.class_name, key, clause[key])
            url += ')'
        if sort != None:
            url += '&order-by='
            if isinstance(sort, list):
                for s in sort: url += self.class_name + ('.%s,' % s)
            else: url += self.class_name + ('.%s' % sort)
        if page != None:
            url += '&page=%d&page-size=%d' % (page[0], page[1])
        data = self.controller.get(url)
        ret = []
        for d in data:
            for class_name in d:
                acidipy_obj = AcidipyObject(**d[class_name]['attributes'])
                acidipy_obj.class_name = class_name
                acidipy_obj.controller = self.controller
                acidipy_obj.is_detail = detail
                if class_name in PREPARE_CLASSES:
                    acidipy_obj.__class__ = globals()[PREPARE_CLASSES[class_name]]
                    acidipy_obj.__patch__()
                ret.append(acidipy_obj)
        return ret
    
    def Class(self, class_name, class_pkey=None, class_ident=None):
        return AcidipyActor(self, class_name, class_pkey, class_ident)
    
    def update(self):
        if not self.controller.put('/api/mo/' + self['dn'] + '.json', data=self.toJson()): raise AcidipyUpdateError(self['dn'])
        return True
    
    def delete(self):
        if not self.controller.delete('/api/mo/' + self['dn'] + '.json'): raise AcidipyDeleteError(self['dn'])
        return True

class AcidipyObjectHealth:
    
    def health(self):
        url = '/api/mo/' + self['dn'] + '.json?rsp-subtree-include=health'
        data = self.controller.get(url)
        for d in data:
            for class_name in d:
                try: hinst = d[class_name]['children'][0]['healthInst']
                except: continue
                return {'dn' : self['dn'], 'name' : self['name'], 'score' : int(hinst['attributes']['cur'])}
        raise AcidipyNonExistHealth(self['dn'])

###############################################################
#  _____ ______   ________  ________  _______   ___          
# |\   _ \  _   \|\   __  \|\   ___ \|\  ___ \ |\  \         
# \ \  \\\__\ \  \ \  \|\  \ \  \_|\ \ \   __/|\ \  \        
#  \ \  \\|__| \  \ \  \\\  \ \  \ \\ \ \  \_|/_\ \  \       
#   \ \  \    \ \  \ \  \\\  \ \  \_\\ \ \  \_|\ \ \  \____  
#    \ \__\    \ \__\ \_______\ \_______\ \_______\ \_______\
#     \|__|     \|__|\|_______|\|_______|\|_______|\|_______|
#
###############################################################

class TenantObject(AcidipyObject, AcidipyObjectHealth):
    
    def __patch__(self):
        self.Filter = FilterActor(self)
        self.Contract = ContractActor(self)
        self.Context = ContextActor(self)
        self.L3Out = L3OutActor(self)
        self.BridgeDomain = BridgeDomainActor(self)
        self.AppProfile = AppProfileActor(self)
        
        
class FilterObject(AcidipyObject):
    
    def __patch__(self):
        self.FilterEntry = FilterEntryActor(self)

class ContractObject(AcidipyObject):
    
    def __patch__(self):
        self.Subject = SubjectActor(self)

class ContextObject(AcidipyObject, AcidipyObjectHealth): pass
     
class L3OutObject(AcidipyObject):
    
    def __patch__(self):
        self.L3Profile = L3ProfileActor(self)
        
    def relate(self, obj, **attributes):
        if isinstance(obj, ContextObject):
            attributes['tnFvCtxName'] = obj['name']
            if self.controller.post('/api/mo/' + self['dn'] + '.json', data=json.dumps({'l3extRsEctx' : {'attributes' : attributes}})): return True
        raise AcidipyRelateError(self['dn'] + ' << >> ' + obj['dn'])
    
class L3ProfileObject(AcidipyObject): pass

class BridgeDomainObject(AcidipyObject, AcidipyObjectHealth):
     
    def __patch__(self):
        self.Subnet = SubnetActor(self)
        
    def relate(self, obj, **attributes):
        if isinstance(obj, ContextObject):
            attributes['tnFvCtxName'] = obj['name']
            if self.controller.post('/api/mo/' + self['dn'] + '.json', data=json.dumps({'fvRsCtx' : {'attributes' : attributes}})): return True
        elif isinstance(obj, L3OutObject):
            attributes['tnL3extOutName'] = obj['name']
            if self.controller.post('/api/mo/' + self['dn'] + '.json', data=json.dumps({'fvRsBDToOut' : {'attributes' : attributes}})): return True
        raise AcidipyRelateError(self['dn'] + ' << >> ' + obj['dn'])
         
class AppProfileObject(AcidipyObject, AcidipyObjectHealth):
     
    def __patch__(self):
        self.EPG = EPGActor(self)

class FilterEntryObject(AcidipyObject): pass

class SubjectObject(AcidipyObject):
    
    def relate(self, obj, **attributes):
        if isinstance(obj, FilterObject):
            attributes['tnVzFilterName'] = obj['name']
            if self.controller.post('/api/mo/' + self['dn'] + '.json', data=json.dumps({'vzRsSubjFiltAtt' : {'attributes' : attributes}})): return True
        raise AcidipyRelateError(self['dn'] + ' << >> ' + obj['dn'])
         
class SubnetObject(AcidipyObject): pass
     
class EPGObject(AcidipyObject, AcidipyObjectHealth):
    
    def __patch__(self):
        self.Endpoint = EndpointActor(self)
    
    def relate(self, obj, **attributes):
        if isinstance(obj, BridgeDomainObject):
            attributes['tnFvBDName'] = obj['name']
            if self.controller.post('/api/mo/' + self['dn'] + '.json', data=json.dumps({'fvRsBd' : {'attributes' : attributes}})): return True
        elif isinstance(obj, ContractObject):
            attributes['tnVzBrCPName'] = obj['name']
            if self.controller.post('/api/mo/' + self['dn'] + '.json', data=json.dumps({'fvRsProv' : {'attributes' : attributes}})): return True
        elif isinstance(obj, ContractObject):
            attributes['tnVzBrCPName'] = obj['name']
            if self.controller.post('/api/mo/' + self['dn'] + '.json', data=json.dumps({'fvRsCons' : {'attributes' : attributes}})): return True
        elif isinstance(obj, PathObject): # need "encap" attribute
            attributes['tDn'] = obj['dn']
            if self.controller.post('/api/mo/' + self['dn'] + '.json', data=json.dumps({'fvRsPathAtt' : {'attributes' : attributes}})): return True
        raise AcidipyRelateError(self['dn'] + ' << >> ' + obj['dn'])
     
class EndpointObject(AcidipyObject): pass

class PodObject(AcidipyObject):
    
    def __patch__(self):
        self.Node = NodeActor(self)
        self.Paths = PathsActor(self)
        self.VPaths = VPathsActor(self)

class NodeObject(AcidipyObject):
    
    def __patch__(self):
        if self.is_detail:
            if self['fabricSt'] == 'active' or self['role'] == 'controller':
                self.System = SystemObject(**self.controller(self['dn'] + '/sys', detail=self.is_detail))
                self.System.class_name = 'topSystem'
                self.System.controller = self.controller
                self.System.is_detail = self.is_detail
                self.System.__patch__()
        else:
            self.System = SystemObject(dn=self['dn'] + '/sys')
            self.System.class_name = 'topSystem'
            self.System.controller = self.controller
            self.System.is_detail = self.is_detail
            self.System.__patch__()

class SystemObject(AcidipyObject):
        
    def __patch__(self):
        self.PhysIf = PhysIfActor(self)
        
class PathsObject(AcidipyObject):
    
    def __patch__(self):
        self.Path = PathActor(self)
        
class VPathsObject(AcidipyObject):
    
    def __patch__(self):
        self.Path = PathActor(self)

class PathObject(AcidipyObject): pass

class PhysIfObject(AcidipyObject): pass
        
#############################################################################################################
#  ________  ________  ________   _________  ________  ________  ___       ___       _______   ________     
# |\   ____\|\   __  \|\   ___  \|\___   ___\\   __  \|\   __  \|\  \     |\  \     |\  ___ \ |\   __  \    
# \ \  \___|\ \  \|\  \ \  \\ \  \|___ \  \_\ \  \|\  \ \  \|\  \ \  \    \ \  \    \ \   __/|\ \  \|\  \   
#  \ \  \    \ \  \\\  \ \  \\ \  \   \ \  \ \ \   _  _\ \  \\\  \ \  \    \ \  \    \ \  \_|/_\ \   _  _\  
#   \ \  \____\ \  \\\  \ \  \\ \  \   \ \  \ \ \  \\  \\ \  \\\  \ \  \____\ \  \____\ \  \_|\ \ \  \\  \| 
#    \ \_______\ \_______\ \__\\ \__\   \ \__\ \ \__\\ _\\ \_______\ \_______\ \_______\ \_______\ \__\\ _\ 
#     \|_______|\|_______|\|__| \|__|    \|__|  \|__|\|__|\|_______|\|_______|\|_______|\|_______|\|__|\|__|
#                                                                                                           
#############################################################################################################

#===============================================================================
# Subscriber
#===============================================================================
class Subscriber(Thread, Task):
    
    def __init__(self, controller):
        Thread.__init__(self)
        Task.__init__(self, 30)
        self.controller = controller
        self.socket = None
        self.handlers = {}
        self.connect()
    
    def connect(self):
        if self.socket != None: self.socket.close()
        for i in range(0, self.controller.retry):
            try: self.socket = create_connection('wss://%s/socket%s' % (self.controller['ip'], self.controller.token), sslopt={'cert_reqs': ssl.CERT_NONE})
            except: continue
            if self.controller.debug: print('Subscribe wss://%s/socket%s' % (self.controller['ip'], self.controller.token))
            return
        raise AcidipySessionError()
    
    def close(self):
        self.socket.close()
        self.stop()
        
    def thread(self):
        try:
            data = json.loads(self.socket.recv())
            subscribe_ids = data['subscriptionId']
            if not isinstance(subscribe_ids, list): subscribe_ids = [subscribe_ids]
            subscribe_data = data['imdata']
        except: self.connect()
        else:
            for sd in subscribe_data:
                for class_name in sd:
                    acidipy_obj = AcidipyObject(**sd[class_name]['attributes'])
                    acidipy_obj.controller = self.controller
                    acidipy_obj.class_name = class_name
                    acidipy_obj.is_detail = True
                    if class_name in PREPARE_CLASSES:
                        acidipy_obj.__class__ = globals()[PREPARE_CLASSES[class_name]]
                        acidipy_obj.__patch__()
                    for subscribe_id in subscribe_ids:
                        try: self.handlers[subscribe_id].subscribe(acidipy_obj['status'], acidipy_obj)
                        except Exception as e:
                            if self.controller.debug: print('Subscribe : {}'.format(str(e)))
                            continue
    
    def task(self):
        for subscribe_id in self.events:
            try: self.controller.get('/api/subscriptionRefresh.json?id=%s' % subscribe_id)
            except: continue
    
    def register(self, handler):
        resp = self.controller.session.get(self.controller.url + '/api/class/%s.json?subscription=yes' % handler.class_name)
        if resp.status_code == 200:
            try:
                data = resp.json()
                subscription_id = data['subscriptionId']
                self.handlers[subscription_id] = handler
                self.start()
                return subscription_id
            except: raise AcidipySubscriptionError()
        else: raise AcidipySubscriptionError()

#===============================================================================
# Controller
#===============================================================================
class Controller(Session, AcidipyObject, Task):
    
    class Actor:
        
        def __init__(self, controller, class_name):
            self.controller = controller
            self.class_name = class_name
            if class_name in PREPARE_CLASSES: self.prepare_class = globals()[PREPARE_CLASSES[class_name]]
            else: self.prepare_class = None
        
        def keys(self):
            if self.class_name in PREPARE_ATTRIBUTES: return PREPARE_ATTRIBUTES[self.class_name]
            url = '/api/class/' + self.class_name + '.json?page=0&page-size=1'
            data = self.controller.get(url)
            try: keys = sorted(data[0][self.class_name]['attributes'].keys())
            except: raise AcidipyAttributesError()
            if 'childAction' in keys: keys.remove('childAction')
            if 'dn' in keys: keys.remove('dn'); keys.insert(0, 'dn')
            if 'name' in keys: keys.remove('name'); keys.insert(0, 'name')
            if 'id' in keys: keys.remove('id'); keys.insert(0, 'id')
            PREPARE_ATTRIBUTES[self.class_name] = keys
            return keys
            
        def list(self, detail=False, sort=None, page=None, **clause):
            url = '/api/node/class/' + self.class_name + '.json?'
            if not detail: url += '&rsp-prop-include=naming-only'
            if len(clause) > 0:
                url += '&query-target-filter=and('
                for key in clause: url += 'eq(%s.%s,"%s"),' % (self.class_name, key, clause[key])
                url += ')'
            if sort != None:
                url += '&order-by='
                if isinstance(sort, list):
                    for s in sort: url += self.class_name + ('.%s,' % s)
                else: url += self.class_name + ('.%s' % sort)
            if page != None:
                url += '&page=%d&page-size=%d' % (page[0], page[1])
            data = self.controller.get(url)
            ret = []
            for d in data:
                for class_name in d:
                    acidipy_obj = AcidipyObject(**d[class_name]['attributes'])
                    acidipy_obj.class_name = class_name
                    acidipy_obj.controller = self.controller
                    acidipy_obj.is_detail = detail
                    if self.prepare_class:
                        acidipy_obj.__class__ = self.prepare_class
                        acidipy_obj.__patch__()
                    ret.append(acidipy_obj)
            return ret
        
        def count(self, **clause):
            url = '/api/node/class/' + self.class_name + '.json?'
            if len(clause) > 0:
                url += 'query-target-filter=and('
                for key in clause: url += 'eq(%s.%s,"%s"),' % (self.class_name, key, clause[key])
                url += ')&'
            url += 'rsp-subtree-include=count'
            data = self.controller.get(url)
            try: return int(data[0]['moCount']['attributes']['count'])
            except: raise AcidipyNonExistCount(self.class_name)
            
        def subscribe(self, handler):
            handler.class_name = self.class_name
            self.controller.subscriber.register(handler)
            
    class ActorHealth:
        
        def health(self):
            url = '/api/node/class/' + self.class_name + '.json?&rsp-subtree-include=health'
            data = self.controller.get(url)
            ret = []
            for d in data:
                for class_name in d:
                    try: hinst = d[class_name]['children'][0]['healthInst']
                    except: continue
                    attrs = d[class_name]['attributes']
                    obj = {'dn' : attrs['dn'], 'name' : attrs['name'], 'score' : int(hinst['attributes']['cur'])}
                    ret.append(obj)
            return ret
    
    class FilterActor(Actor):
        def __init__(self, controller): Controller.Actor.__init__(self, controller, 'vzFilter')
    
    class ContractActor(Actor):
        def __init__(self, controller): Controller.Actor.__init__(self, controller, 'vzBrCP')
    
    class ContextActor(Actor, ActorHealth):
        def __init__(self, controller): Controller.Actor.__init__(self, controller, 'fvCtx')
    
    class L3OutActor(Actor):
        def __init__(self, controller): Controller.Actor.__init__(self, controller, 'l3extOut')
    
    class L3ProfileActor(Actor):
        def __init__(self, controller): Controller.Actor.__init__(self, controller, 'l3extInstP')
        
    class BridgeDomainActor(Actor, ActorHealth):
        def __init__(self, controller): Controller.Actor.__init__(self, controller, 'fvBD')
    
    class AppProfileActor(Actor, ActorHealth):
        def __init__(self, controller): Controller.Actor.__init__(self, controller, 'fvAp')
    
    class FilterEntryActor(Actor):
        def __init__(self, controller): Controller.Actor.__init__(self, controller, 'vzEntry')
    
    class SubjectActor(Actor):
        def __init__(self, controller): Controller.Actor.__init__(self, controller, 'vzSubj')
    
    class SubnetActor(Actor):
        def __init__(self, controller): Controller.Actor.__init__(self, controller, 'fvSubnet')
    
    class EPGActor(Actor, ActorHealth):
        def __init__(self, controller): Controller.Actor.__init__(self, controller, 'fvAEPg')
        
    class EndpointActor(Actor):
        def __init__(self, controller): Controller.Actor.__init__(self, controller, 'fvCEp')
        
    class NodeActor(Actor):
        def __init__(self, controller): Controller.Actor.__init__(self, controller, 'fabricNode')
        def health(self):
            url = '/api/node/class/healthInst.json?query-target-filter=wcard(healthInst.dn,"^sys/health")'
            data = self.controller.get(url)
            ret = []
            for d in data:
                for class_name in d:
                    attrs = d[class_name]['attributes']
                    obj = {'dn' : attrs['dn'].replace('/sys/health', ''), 'name' : attrs['dn'].split('/')[2].replace('node-', ''), 'score' : int(attrs['cur'])}
                    ret.append(obj)
            return ret
    
    class PathsActor(Actor):
        def __init__(self, controller): Controller.Actor.__init__(self, controller, 'fabricPathEpCont')
    
    class VPathsActor(Actor):
        def __init__(self, controller): Controller.Actor.__init__(self, controller, 'fabricProtPathEpCont')
    
    class PathActor(Actor):
        def __init__(self, controller): Controller.Actor.__init__(self, controller, 'fabricPathEp')
    
    class SystemActor(Actor):
        def __init__(self, controller): Controller.Actor.__init__(self, controller, 'topSystem')
    
    class PhysIfActor(Actor):
        def __init__(self, controller): Controller.Actor.__init__(self, controller, 'l1PhysIf')
        def health(self):
            url = '/api/node/class/healthInst.json?query-target-filter=wcard(healthInst.dn,"phys/health")'
            data = self.controller.get(url)
            ret = []
            for d in data:
                for class_name in d:
                    attrs = d[class_name]['attributes']
                    obj = {'dn' : attrs['dn'].replace('/phys/health', ''), 'name' : attrs['dn'].split('[')[1].replace(']/phys/health', ''), 'score' : int(attrs['cur'])}
                    ret.append(obj)
            return ret
    
    class FaultActor(Actor):
        def __init__(self, controller): Controller.Actor.__init__(self, controller, 'faultInfo')
    
    class ActorDesc(dict):
        def __init__(self, controller, dn): dict.__init__(self, dn=dn); self.controller = controller
    
    def __init__(self, ip, user, pwd, conns=1, conn_max=2, retry=3, debug=False, week=False):
        Session.__init__(self,
                         ip=ip,
                         user=user,
                         pwd=pwd,
                         conns=conns,
                         conn_max=conn_max,
                         retry=retry,
                         debug=debug,
                         week=week)
        AcidipyObject.__init__(self,
                               ip=ip,
                               user=user,
                               pwd=pwd,
                               conns=conns,
                               conn_max=conn_max)
        Task.__init__(self, 180)
        
        self.class_name = 'Controller'
        self.scheduler = Scheduler(10)
        self.subscriber = Subscriber(self)
        
        self.Tenant = TenantActor(Controller.ActorDesc(self, 'uni'))
        
        self.Filter = Controller.FilterActor(self)
        self.Contract = Controller.ContractActor(self)
        self.Context = Controller.ContextActor(self)
        self.L3Out = Controller.L3OutActor(self)
        self.L3Profile = Controller.L3ProfileActor(self)
        self.BridgeDomain = Controller.BridgeDomainActor(self)
        self.AppProfile = Controller.AppProfileActor(self)
        self.FilterEntry = Controller.FilterEntryActor(self)
        self.Subject = Controller.SubjectActor(self)
        self.Subnet = Controller.SubnetActor(self)
        self.EPG = Controller.EPGActor(self)
        self.Endpoint = Controller.EndpointActor(self)
        
        self.Pod = PodActor(Controller.ActorDesc(self, 'topology'))
        
        self.Node = Controller.NodeActor(self)
        self.Paths = Controller.PathsActor(self)
        self.VPaths = Controller.VPathsActor(self)
        self.Path = Controller.PathActor(self)
        self.System = Controller.SystemActor(self)
        self.PhysIf = Controller.PhysIfActor(self)
        
        self.Fault = Controller.FaultActor(self)
        
        self.scheduler.register(self)
        self.scheduler.register(self.subscriber)
        self.scheduler.start()
        
    def close(self):
        self.subscriber.close()
        self.scheduler.stop()
        Session.close(self)
                
    def task(self): self.refresh()
        
    def detail(self): return self
    
    def health(self):
        url = '/api/node/class/fabricHealthTotal.json?query-target-filter=eq(fabricHealthTotal.dn,"topology/health")'
        data = self.get(url)
        for d in data:
            for class_name in d:
                attrs = d[class_name]['attributes']
                return {'dn' : 'topology', 'name' : 'Total', 'score' : int(attrs['cur'])}
        raise AcidipyNonExistHealth('topology')

    def Class(self, class_name):
        return Controller.Actor(self, class_name)
    
    def __call__(self, dn, detail=False):
        url = '/api/mo/' + dn + '.json'
        if not detail: url += '?rsp-prop-include=naming-only'
        data = self.get(url)
        for d in data:
            for class_name in d:
                acidipy_obj = AcidipyObject(**d[class_name]['attributes'])
                acidipy_obj.controller = self
                acidipy_obj.class_name = class_name
                acidipy_obj.is_detail = detail
                if class_name in PREPARE_CLASSES:
                    acidipy_obj.__class__ = globals()[PREPARE_CLASSES[class_name]]
                    acidipy_obj.__patch__()
                return acidipy_obj
        raise AcidipyNonExistData(dn)

class MultiDomain(dict):
    
    class Actor:
        
        def __init__(self, multi_dom, actor_name):
            self.multi_dom = multi_dom
            self.actor_name = actor_name
        
        def list(self, detail=False, sort=None, page=None, **clause):
            ret = {}
            for dom_name in self.multi_dom: ret[dom_name] = self.multi_dom[dom_name].__getattribute__(self.actor_name).list(detail, sort, page, **clause)
            return ret 
            
            # GEVENT
#             ret = {}; fetchs = []
#             def fetch(multi_dom, dom_name, actor_name, detail, sort, page, clause, ret): ret[dom_name] = multi_dom[dom_name].__getattribute__(actor_name).list(detail, sort, page, **clause) 
#             for dom_name in self.multi_dom: fetchs.append(gevent.spawn(fetch, self.multi_dom, dom_name, self.actor_name, detail, sort, page, clause, ret))
#             gevent.joinall(fetchs)
#             return ret
        
        def health(self):
            ret = {}
            for dom_name in self.multi_dom: ret[dom_name] = self.multi_dom[dom_name].__getattribute__(self.actor_name).health()
            return ret 
            
            # GEVENT
#             ret = {}; fetchs = []
#             def fetch(multi_dom, dom_name, actor_name, ret): ret[dom_name] = multi_dom[dom_name].__getattribute__(actor_name).health() 
#             for dom_name in self.multi_dom: fetchs.append(gevent.spawn(fetch, self.multi_dom, dom_name, self.actor_name, ret))
#             gevent.joinall(fetchs)
#             return ret
            
        def count(self, **clause):
            ret = {}
            for dom_name in self.multi_dom: ret[dom_name] = self.multi_dom[dom_name].__getattribute__(self.actor_name).count(**clause)
            return ret 
            
            # GEVENT
#             ret = {}; fetchs = []
#             def fetch(multi_dom, dom_name, actor_name, clause, ret): ret[dom_name] = multi_dom[dom_name].__getattribute__(actor_name).count(**clause) 
#             for dom_name in self.multi_dom: fetchs.append(gevent.spawn(fetch, self.multi_dom, dom_name, self.actor_name, clause, ret))
#             gevent.joinall(fetchs)
#             return ret
    
    class ClassActor:
        
        def __init__(self, multi_dom, class_name):
            self.multi_dom = multi_dom
            self.class_name = class_name
            
        def list(self, detail=False, sort=None, page=None, **clause):
            ret = {}
            for dom_name in self.multi_dom: ret[dom_name] = self.multi_dom[dom_name].Class(self.class_name).list(detail, sort, page, **clause)
            return ret 
        
            # GEVENT
#             ret = {}; fetchs = []
#             def fetch(multi_dom, dom_name, class_name, detail, sort, page, clause, ret): ret[dom_name] = multi_dom[dom_name].Class(class_name).list(detail, sort, page, **clause)
#             for dom_name in self.multi_dom: fetchs.append(gevent.spawn(fetch, self.multi_dom, dom_name, self.class_name, detail, sort, page, clause, ret))
#             gevent.joinall(fetchs)
#             return ret
        
        def count(self, **clause):
            ret = {}
            for dom_name in self.multi_dom: ret[dom_name] = self.multi_dom[dom_name].Class(self.class_name).count(*clause)
            return ret
        
            # GEVENT
#             ret = {}; fetchs = []
#             def fetch(multi_dom, dom_name, class_name, clause, ret): ret[dom_name] = multi_dom[dom_name].Class(class_name).count(**clause)
#             for dom_name in self.multi_dom: fetchs.append(gevent.spawn(fetch, self.multi_dom, dom_name, self.class_name, clause, ret))
#             gevent.joinall(fetchs)
#             return ret
    
    def __init__(self, conns=1, conn_max=2, retry=3, debug=False, week=False):
        dict.__init__(self)
        self.conns = conns
        self.conn_max = conn_max
        self.retry = retry
        self.debug = debug
        self.week = week
        
        self.Tenant = MultiDomain.Actor(self, 'Tenant')
        self.Filter = MultiDomain.Actor(self, 'Filter')
        self.Contract = MultiDomain.Actor(self, 'Contract')
        self.Context = MultiDomain.Actor(self, 'Context')
        self.L3Out = MultiDomain.Actor(self, 'L3Out')
        self.L3Profile = MultiDomain.Actor(self, 'L3Profile')
        self.BridgeDomain = MultiDomain.Actor(self, 'BridgeDomain')
        self.AppProfile = MultiDomain.Actor(self, 'AppProfile')
        self.FilterEntry = MultiDomain.Actor(self, 'FilterEntry')
        self.Subject = MultiDomain.Actor(self, 'Subject')
        self.Subnet = MultiDomain.Actor(self, 'Subnet')
        self.EPG = MultiDomain.Actor(self, 'EPG')
        self.Endpoint = MultiDomain.Actor(self, 'Endpoint')
        
        self.Pod = MultiDomain.Actor(self, 'Pod')
        
        self.Node = MultiDomain.Actor(self, 'Node')
        self.Paths = MultiDomain.Actor(self, 'Paths')
        self.VPaths = MultiDomain.Actor(self, 'VPaths')
        self.Path = MultiDomain.Actor(self, 'Path')
        self.System = MultiDomain.Actor(self, 'System')
        self.PhysIf = MultiDomain.Actor(self, 'PhysIf')
        
        self.Fault = MultiDomain.Actor(self, 'Fault')
    
    def Class(self, class_name):
        return MultiDomain.ClassActor(self, class_name)
    
    def detail(self): return self
    
    def health(self):
        ret = {}
        for dom_name in self: ret[dom_name] = self[dom_name].health()
        return ret
        
    def addDomain(self, domain_name, ip, user, pwd, conns=None, conn_max=None, retry=None, debug=None, week=None):
        if domain_name in self: return False
        opts = {'ip' : ip, 'user' : user, 'pwd' : pwd}
        opts['conns'] = conns if conns != None else self.conns
        opts['conn_max'] = conn_max if conn_max != None else self.conn_max
        opts['retry'] = retry if retry != None else self.retry
        opts['debug'] = debug if debug != None else self.debug
        opts['week'] = week if week != None else self.week
        try: ctrl = Controller(**opts)
        except: return False
        self[domain_name] = ctrl
        return True
    
    def delDomain(self, domain_name):
        if domain_name not in self: return False
        self[domain_name].close()
        self.pop(domain_name)
        return True
    
    def close(self):
        dom_names = self.keys()
        for dom_name in dom_names: self.delDomain(dom_name)
        
