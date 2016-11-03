'''
Created on 2016. 10. 18.

@author: "comfact"
'''

import re
import ssl
import time
import json
import threading

from websocket import create_connection
try: from Queue import Queue
except: from queue import Queue

from .session import Session
from .static import *

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

#===============================================================================
# Subscribe Actor
#===============================================================================
class SubscribeActor:
    
    def subscribe(self, handler):
        handler.class_name = self.class_name
        self.controller.subscriber.register(handler)

#===============================================================================
# Class Actor
#===============================================================================
class AcidipyActor:
    
    def __init__(self, parent, class_name, class_pkey=None, class_ident=None):
        self.parent = parent
        self.controller = parent.controller
        self.class_name = class_name
        self.class_pkey = class_pkey
        self.class_ident = class_ident
        if class_name in PREPARE_CLASSES: self.prepare_class = globals()[PREPARE_CLASSES[class_name]]
        else: self.prepare_class = None

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
    
    def count(self):
        url = '/api/node/class/' + self.class_name + '.json?query-target-filter=wcard(' + self.class_name + '.dn,"' + self.parent['dn'] + '/.*")&rsp-subtree-include=count'
        data = self.controller.get(url)
        try: return int(data[0]['moCount']['attributes']['count'])
        except: raise AcidipyNonExistCount(self.class_name)

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
    
class AcidipyActorCreate:
    
    def create(self, **attributes):
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

class TenantActor(AcidipyActor, AcidipyActorHealth, AcidipyActorCreate, SubscribeActor):
    def __init__(self, parent): AcidipyActor.__init__(self, parent, 'fvTenant', 'name', '/tn-%s')
    
class FilterActor(AcidipyActor, AcidipyActorCreate):
    def __init__(self, parent): AcidipyActor.__init__(self, parent, 'vzFilter', 'name', '/flt-%s')

class ContractActor(AcidipyActor, AcidipyActorCreate):
    def __init__(self, parent): AcidipyActor.__init__(self, parent, 'vzBrCP', 'name', '/brc-%s')

class ContextActor(AcidipyActor, AcidipyActorHealth, AcidipyActorCreate):
    def __init__(self, parent): AcidipyActor.__init__(self, parent, 'fvCtx', 'name', '/ctx-%s')
    
class L3ExternalActor(AcidipyActor, AcidipyActorCreate):
    def __init__(self, parent): AcidipyActor.__init__(self, parent, 'l3extOut', 'name', '/out-%s')
    
class BridgeDomainActor(AcidipyActor, AcidipyActorHealth, AcidipyActorCreate):
    def __init__(self, parent): AcidipyActor.__init__(self, parent, 'fvBD', 'name', '/BD-%s')

class AppProfileActor(AcidipyActor, AcidipyActorHealth, AcidipyActorCreate):
    def __init__(self, parent): AcidipyActor.__init__(self, parent, 'fvAp', 'name', '/ap-%s')

class FilterEntryActor(AcidipyActor, AcidipyActorCreate):
    def __init__(self, parent): AcidipyActor.__init__(self, parent, 'vzEntry', 'name', '/e-%s')

class SubjectActor(AcidipyActor, AcidipyActorCreate):
    def __init__(self, parent): AcidipyActor.__init__(self, parent, 'vzSubj', 'name', '/subj-%s')

class SubnetActor(AcidipyActor, AcidipyActorCreate):
    def __init__(self, parent): AcidipyActor.__init__(self, parent, 'fvSubnet', 'ip', '/subnet-[%s]')

class EPGActor(AcidipyActor, AcidipyActorHealth, AcidipyActorCreate):
    def __init__(self, parent): AcidipyActor.__init__(self, parent, 'fvAEPg', 'name', '/epg-%s')

class EndpointActor(AcidipyActor, AcidipyActorCreate):
    def __init__(self, parent): AcidipyActor.__init__(self, parent, 'fvCEp', 'name', '/cep-%s')

class PodActor(AcidipyActor, SubscribeActor):
    def __init__(self, parent): AcidipyActor.__init__(self, parent, 'fabricPod', 'id', '/pod-%s')
    def health(self):
        url = '/api/node/class/fabricHealthTotal.json?query-target-filter=ne(fabricHealthTotal.dn,"topology/health")'
        data = self.controller.get(url)
        ret = []
        for d in data:
            for class_name in d:
                attrs = d[class_name]['attributes']
                if self.parent['dn'] in attrs['dn']:
                    obj = {'dn' : attrs['dn'].repalce('/health', ''), 'name' : attrs['dn'].split('/')[1].replace('pod-', ''), 'score' : int(attrs['cur'])}
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
                    obj = {'dn' : attrs['dn'].repalce('/sys/health', ''), 'name' : attrs['dn'].split('/')[2].replace('node-', ''), 'score' : int(attrs['cur'])}
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

#===============================================================================
# Controller Actor
#===============================================================================
class ControllerActor:
        
    def __init__(self, controller, class_name):
        self.controller = controller
        self.class_name = class_name
        if class_name in PREPARE_CLASSES: self.prepare_class = globals()[PREPARE_CLASSES[class_name]]
        else: self.prepare_class = None
        
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
    
    def count(self):
        url = '/api/node/class/' + self.class_name + '.json?rsp-subtree-include=count'
        data = self.controller.get(url)
        try: return int(data[0]['moCount']['attributes']['count'])
        except: raise AcidipyNonExistCount(self.class_name)
        
class ControllerActorHealth:
    
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

class ControllerFilterActor(ControllerActor, SubscribeActor):
    def __init__(self, controller): ControllerActor.__init__(self, controller, 'vzFilter')

class ControllerContractActor(ControllerActor, SubscribeActor):
    def __init__(self, controller): ControllerActor.__init__(self, controller, 'vzBrCP')

class ControllerContextActor(ControllerActor, ControllerActorHealth, SubscribeActor):
    def __init__(self, controller): ControllerActor.__init__(self, controller, 'fvCtx')

class ControllerL3ExternalActor(ControllerActor, SubscribeActor):
    def __init__(self, controller): ControllerActor.__init__(self, controller, 'l3extOut')
    
class ControllerBridgeDomainActor(ControllerActor, ControllerActorHealth, SubscribeActor):
    def __init__(self, controller): ControllerActor.__init__(self, controller, 'fvBD')

class ControllerAppProfileActor(ControllerActor, ControllerActorHealth, SubscribeActor):
    def __init__(self, controller): ControllerActor.__init__(self, controller, 'fvAp')

class ControllerFilterEntryActor(ControllerActor, SubscribeActor):
    def __init__(self, controller): ControllerActor.__init__(self, controller, 'vzEntry')

class ControllerSubjectActor(ControllerActor, SubscribeActor):
    def __init__(self, controller): ControllerActor.__init__(self, controller, 'vzSubj')

class ControllerSubnetActor(ControllerActor, SubscribeActor):
    def __init__(self, controller): ControllerActor.__init__(self, controller, 'fvSubnet')

class ControllerEPGActor(ControllerActor, ControllerActorHealth, SubscribeActor):
    def __init__(self, controller): ControllerActor.__init__(self, controller, 'fvAEPg')
    
class ControllerEndpointActor(ControllerActor, SubscribeActor):
    def __init__(self, controller): ControllerActor.__init__(self, controller, 'fvCEp')
    
class ControllerNodeActor(ControllerActor, SubscribeActor):
    def __init__(self, controller): ControllerActor.__init__(self, controller, 'fabricNode')
    def health(self):
        url = '/api/node/class/healthInst.json?query-target-filter=wcard(healthInst.dn,"^sys/health")'
        data = self.controller.get(url)
        ret = []
        for d in data:
            for class_name in d:
                attrs = d[class_name]['attributes']
                obj = {'dn' : attrs['dn'].repalce('/sys/health', ''), 'name' : attrs['dn'].split('/')[2].replace('node-', ''), 'score' : int(attrs['cur'])}
                ret.append(obj)
        return ret

class ControllerPathsActor(ControllerActor, SubscribeActor):
    def __init__(self, controller): ControllerActor.__init__(self, controller, 'fabricPathEpCont')

class ControllerVPathsActor(ControllerActor, SubscribeActor):
    def __init__(self, controller): ControllerActor.__init__(self, controller, 'fabricProtPathEpCont')

class ControllerPathActor(ControllerActor, SubscribeActor):
    def __init__(self, controller): ControllerActor.__init__(self, controller, 'fabricPathEp')

class ControllerSystemActor(ControllerActor, SubscribeActor):
    def __init__(self, controller): ControllerActor.__init__(self, controller, 'topSystem')

class ControllerPhysIfActor(ControllerActor, SubscribeActor):
    def __init__(self, controller): ControllerActor.__init__(self, controller, 'l1PhysIf')
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

class AcidipyObjectParent:
    
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

class AcidipyObjectChildren:
    
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

class AcidipyObjectModify:
    
    def update(self):
        if not self.controller.put('/api/mo/' + self['dn'] + '.json', data=self.toJson()): raise AcidipyUpdateError(self['dn'])
        return True
    
    def delete(self):
        if not self.controller.delete('/api/mo/' + self['dn'] + '.json'): raise AcidipyDeleteError(self['dn'])
        return True

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

#===============================================================================
# Uni Models
#===============================================================================
class TenantObject(AcidipyObject, AcidipyObjectChildren, AcidipyObjectHealth, AcidipyObjectModify):
    
    def __patch__(self):
        self.Filter = FilterActor(self)
        self.Contract = ContractActor(self)
        self.Context = ContextActor(self)
        self.L3External = L3ExternalActor(self)
        self.BridgeDomain = BridgeDomainActor(self)
        self.AppProfile = AppProfileActor(self)
        
class FilterObject(AcidipyObject, AcidipyObjectParent, AcidipyObjectChildren, AcidipyObjectModify):
    
    def __patch__(self):
        self.FilterEntry = FilterEntryActor(self)

class ContractObject(AcidipyObject, AcidipyObjectParent, AcidipyObjectChildren, AcidipyObjectModify):
    
    def __patch__(self):
        self.Subject = SubjectActor(self)

class ContextObject(AcidipyObject, AcidipyObjectParent, AcidipyObjectChildren, AcidipyObjectHealth, AcidipyObjectModify): pass
     
class L3ExternalObject(AcidipyObject, AcidipyObjectParent, AcidipyObjectChildren, AcidipyObjectModify):
    
    def relate2Context(self, vrf_object, **attributes):
        if isinstance(vrf_object, ContextObject):
            attributes['tnFvCtxName'] = vrf_object['name']
            if self.controller.post('/api/mo/' + self['dn'] + '.json', data=json.dumps({'l3extRsEctx' : {'attributes' : attributes}})): return True
        raise AcidipyRelateError(self['dn'] + ' << >> ' + vrf_object['dn'])

class BridgeDomainObject(AcidipyObject, AcidipyObjectParent, AcidipyObjectChildren, AcidipyObjectHealth, AcidipyObjectModify):
     
    def __patch__(self):
        self.Subnet = SubnetActor(self)
         
    def relate2Context(self, vrf_object, **attributes):
        if isinstance(vrf_object, ContextObject):
            attributes['tnFvCtxName'] = vrf_object['name']
            if self.controller.post('/api/mo/' + self['dn'] + '.json', data=json.dumps({'fvRsCtx' : {'attributes' : attributes}})): return True
        raise AcidipyRelateError(self['dn'] + ' << >> ' + vrf_object['dn'])
    
    def relate2L3External(self, out_object, **attributes):
        if isinstance(out_object, L3ExternalObject):
            attributes['tnL3extOutName'] = out_object['name']
            if self.controller.post('/api/mo/' + self['dn'] + '.json', data=json.dumps({'fvRsBDToOut' : {'attributes' : attributes}})): return True
        raise AcidipyRelateError(self['dn'] + ' << >> ' + out_object['dn']) 
 
class AppProfileObject(AcidipyObject, AcidipyObjectParent, AcidipyObjectChildren, AcidipyObjectHealth, AcidipyObjectModify):
     
    def __patch__(self):
        self.EPG = EPGActor(self)

class FilterEntryObject(AcidipyObject, AcidipyObjectParent, AcidipyObjectChildren, AcidipyObjectModify): pass

class SubjectObject(AcidipyObject, AcidipyObjectParent, AcidipyObjectChildren, AcidipyObjectModify):
    
    def relate2Filter(self, flt_object, **attributes):
        if isinstance(flt_object, FilterObject):
            attributes['tnVzFilterName'] = flt_object['name']
            if self.controller.post('/api/mo/' + self['dn'] + '.json', data=json.dumps({'vzRsSubjFiltAtt' : {'attributes' : attributes}})): return True
        raise AcidipyRelateError(self['dn'] + ' << >> ' + flt_object['dn'])
         
class SubnetObject(AcidipyObject, AcidipyObjectParent, AcidipyObjectChildren, AcidipyObjectModify): pass
     
class EPGObject(AcidipyObject, AcidipyObjectParent, AcidipyObjectChildren, AcidipyObjectHealth, AcidipyObjectModify):
    
    def __patch__(self):
        self.Endpoint = EndpointActor(self)
     
    def relate2BridgeDomain(self, bd_object, **attributes):
        if isinstance(bd_object, BridgeDomainObject):
            attributes['tnFvBDName'] = bd_object['name']
            if self.controller.post('/api/mo/' + self['dn'] + '.json', data=json.dumps({'fvRsBd' : {'attributes' : attributes}})): return True
        raise AcidipyRelateError(self['dn'] + ' << >> ' + bd_object['dn'])
    
    def relate2Provider(self, ctr_object, **attributes):
        if isinstance(ctr_object, ContractObject):
            attributes['tnVzBrCPName'] = ctr_object['name']
            if self.controller.post('/api/mo/' + self['dn'] + '.json', data=json.dumps({'fvRsProv' : {'attributes' : attributes}})): return True
        raise AcidipyRelateError(self['dn'] + ' << >> ' + ctr_object['dn'])
    
    def relate2Consumer(self, ctr_object, **attributes):
        if isinstance(ctr_object, ContractObject):
            attributes['tnVzBrCPName'] = ctr_object['name']
            if self.controller.post('/api/mo/' + self['dn'] + '.json', data=json.dumps({'fvRsCons' : {'attributes' : attributes}})): return True
        raise AcidipyRelateError(self['dn'] + ' << >> ' + ctr_object['dn'])
    
    def relate2StaticPath(self, path_object, encap, **attributes):
        if isinstance(path_object, PathObject):
            attributes['tDn'] = path_object['dn']
            attributes['encap'] = encap
            if self.controller.post('/api/mo/' + self['dn'] + '.json', data=json.dumps({'fvRsPathAtt' : {'attributes' : attributes}})): return True
        raise AcidipyRelateError(self['dn'] + ' << >> ' + path_object['dn'])

class EndpointObject(AcidipyObject, AcidipyObjectParent): pass

#===============================================================================
# Topo Models
#===============================================================================
class PodObject(AcidipyObject, AcidipyObjectChildren):
    
    def __patch__(self):
        self.Node = NodeActor(self)
        self.Paths = PathsActor(self)
        self.VPaths = VPathsActor(self)

class NodeObject(AcidipyObject, AcidipyObjectParent, AcidipyObjectChildren):
    
    def __patch__(self):
        if self.is_detail: self.System = SystemObject(**self.controller(self['dn'] + '/sys', detail=self.is_detail))
        else: self.System = SystemObject(dn=self['dn'] + '/sys')
        self.System.controller = self.controller
        self.System.is_detail = self.is_detail
        self.System.__patch__()

class SystemObject(AcidipyObject, AcidipyObjectParent, AcidipyObjectChildren):
        
    def __patch__(self):
        self.PhysIf = PhysIfActor(self)
        
class PathsObject(AcidipyObject, AcidipyObjectParent, AcidipyObjectChildren):
    
    def __patch__(self):
        self.Path = PathActor(self)
        
class VPathsObject(AcidipyObject, AcidipyObjectParent, AcidipyObjectChildren):
    
    def __patch__(self):
        self.Path = PathActor(self)

class PathObject(AcidipyObject, AcidipyObjectParent): pass

class PhysIfObject(AcidipyObject, AcidipyObjectParent): pass
        

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
# System Thread
#===============================================================================
class SystemThread(threading.Thread):
    
    def __init__(self):
        threading.Thread.__init__(self)
        self._tb_sw = False
        
    def start(self):
        if not self._tb_sw:
            self._tb_sw = True
            threading.Thread.start(self)
    
    def stop(self):
        if self._tb_sw:
            self._tb_sw = False
            self._Thread__stop()
            self.join()
        
    def run(self):
        while self._tb_sw: self.thread()
            
    def thread(self): pass

#===============================================================================
# Scheduler
#===============================================================================
class SchedTask:
    def __init__(self, tick):
        self.schedtask_tick = tick
        self.schedtask_cur = 0
        
    def __sched_wrapper__(self, sched_tick):
        self.schedtask_cur += sched_tick
        if self.schedtask_cur >= self.schedtask_tick:
            self.schedtask_cur = 0
            self.sched()
            
    def sched(self): pass

class Scheduler(SystemThread):
    
    def __init__(self, tick):
        SystemThread.__init__(self)
        self.tick = tick
        self.queue = []
        self.regreq = Queue()
    
    def thread(self):
        start_time = time.time()
        while not self.regreq.empty():
            task = self.regreq.get()
            self.queue.append(task)
        for task in self.queue:
            try: task.__sched_wrapper__(self.tick)
            except: continue
        end_time = time.time()
        sleep_time = self.tick - (end_time - start_time)
        if sleep_time > 0: time.sleep(sleep_time)
        
            
    def register(self, task):
        self.regreq.put(task)
        
    def unregister(self, task):
        sw_stat = self._tb_sw
        if sw_stat: self.stop()
        if task in self.queue: self.queue.remove(task)
        if sw_stat: self.start()

#===============================================================================
# Subscriber
#===============================================================================

class Subscriber(SystemThread, SchedTask):
    
    def __init__(self, controller):
        SystemThread.__init__(self)
        SchedTask.__init__(self, 30)
        self.controller = controller
        try: self.socket = create_connection('wss://%s/socket%s' % (self.controller['ip'], self.controller.token), sslopt={'cert_reqs': ssl.CERT_NONE})
        except: raise AcidipySessionError()
        self.handlers = {}
        
    def close(self):
        self.socket.close()
        self.stop()
        
    def thread(self):
        try:
            data = json.loads(self.socket.recv())
            subscribe_ids = data['subscriptionId']
            if not isinstance(subscribe_ids, list): subscribe_ids = [subscribe_ids]
            subscribe_data = data['imdata']
        except: pass
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
    
    def sched(self):
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

class SubscribeHandler:
    def subscribe(self, status, obj): pass

#===============================================================================
# Controller
#===============================================================================
class Controller(Session, AcidipyObject, SchedTask):
    
    class ControllerActorDesc(dict):
        def __init__(self, controller, dn): dict.__init__(self, dn=dn); self.controller = controller
    
    def __init__(self, ip, user, pwd, conns=1, conn_max=2, debug=False, week=False):
        Session.__init__(self,
                         ip=ip,
                         user=user,
                         pwd=pwd,
                         conns=conns,
                         conn_max=conn_max,
                         debug=debug,
                         week=week)
        AcidipyObject.__init__(self,
                               ip=ip,
                               user=user,
                               pwd=pwd)
        SchedTask.__init__(self, 300)
        
        self.class_name = 'Controller'
        self.scheduler = Scheduler(10)
        self.subscriber = Subscriber(self)
        
        self.Tenant = TenantActor(Controller.ControllerActorDesc(self, 'uni'))
        
        self.Filter = ControllerFilterActor(self)
        self.Contract = ControllerContractActor(self)
        self.Context = ControllerContextActor(self)
        self.L3External = ControllerL3ExternalActor(self)
        self.BridgeDomain = ControllerBridgeDomainActor(self)
        self.AppProfile = ControllerAppProfileActor(self)
        self.FilterEntry = ControllerFilterEntryActor(self)
        self.Subject = ControllerSubjectActor(self)
        self.Subnet = ControllerSubnetActor(self)
        self.EPG = ControllerEPGActor(self)
        self.Endpoint = ControllerEndpointActor(self)
        
        self.Pod = PodActor(Controller.ControllerActorDesc(self, 'topology'))
        
        self.Node = ControllerNodeActor(self)
        self.Paths = ControllerPathsActor(self)
        self.VPaths = ControllerVPathsActor(self)
        self.Path = ControllerPathActor(self)
        self.System = ControllerSystemActor(self)
        self.PhysIf = ControllerPhysIfActor(self)
        
        self.scheduler.register(self)
        self.scheduler.register(self.subscriber)
        self.scheduler.start()
        
    def close(self):
        self.subscriber.close()
        self.scheduler.stop()
        Session.close(self)
                
    def sched(self): self.refresh()
        
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
        return ControllerActor(self, class_name)
    
    def __call__(self, dn, detail=False):
        url = '/api/mo/' + dn + '.json'
        if not detail: url += '?rsp-prop-include=naming-only'
        data = self.get(url)
        for d in data:
            for class_name in d:
                acidipy_obj = AcidipyObject(**d[class_name]['attributes'])
                acidipy_obj.controller = self
                acidipy_obj.class_name = class_name
                acidipy_obj.detail = detail
                if class_name in PREPARE_CLASSES:
                    acidipy_obj.__class__ = globals()[PREPARE_CLASSES[class_name]]
                    acidipy_obj.__patch__()
                return acidipy_obj
        raise AcidipyNonExistData(dn)

