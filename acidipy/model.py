'''
Created on 2016. 10. 18.

@author: "comfact"
'''

import re
import ssl
import json
import gevent

from jzlib import Inventory
from pygics import Task, Rest
from websocket import create_connection

from .session import Session
from .static import *

#  ________  ________  ________  _________  ________  ________  ________ _________   
# |\   __  \|\   __  \|\   ____\|\___   ___\\   __  \|\   __  \|\   ____\\___   ___\ 
# \ \  \|\  \ \  \|\ /\ \  \___|\|___ \  \_\ \  \|\  \ \  \|\  \ \  \___\|___ \  \_| 
#  \ \   __  \ \   __  \ \_____  \   \ \  \ \ \   _  _\ \   __  \ \  \       \ \  \  
#   \ \  \ \  \ \  \|\  \|____|\  \   \ \  \ \ \  \\  \\ \  \ \  \ \  \____   \ \  \ 
#    \ \__\ \__\ \_______\____\_\  \   \ \__\ \ \__\\ _\\ \__\ \__\ \_______\  \ \__\
#     \|__|\|__|\|_______|\_________\   \|__|  \|__|\|__|\|__|\|__|\|_______|   \|__|
#                        \|_________|                                                

#===============================================================================
# Global Class
#===============================================================================
class AciGlobalClass(Inventory):
    
    def __init__(self, class_name):
        self.class_name = class_name
        if class_name in PREPARE_CLASSES: self.prepare_class = globals()[PREPARE_CLASSES[class_name]]
        else: self.prepare_class = None
    
    def keys(self):
        controller = ~self
        if self.class_name in PREPARE_ATTRIBUTES: return PREPARE_ATTRIBUTES[self.class_name]
        url = '/api/class/' + self.class_name + '.json?page=0&page-size=1'
        data = controller.get(url)
        try: keys = sorted(data[0][self.class_name]['attributes'].keys())
        except: raise ExceptAcidipyAttributes()
        if 'childAction' in keys: keys.remove('childAction')
        if 'dn' in keys: keys.remove('dn'); keys.insert(0, 'dn')
        if 'name' in keys: keys.remove('name'); keys.insert(0, 'name')
        if 'id' in keys: keys.remove('id'); keys.insert(0, 'id')
        PREPARE_ATTRIBUTES[self.class_name] = keys
        return keys
        
    def list(self, detail=False, sort=None, page=None, **clause):
        controller = ~self
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
        try: data = controller.get(url)
        except Exception as e: raise ExceptAcidipyRetriveObject(controller, self.class_name, e)
        ret = []
        for d in data:
            for class_name in d:
                obj = AciObject(**d[class_name]['attributes'])
                obj.class_name = class_name
                obj.controller = controller
                obj.is_detail = detail
                if self.prepare_class:
                    obj.__class__ = self.prepare_class
                    obj.__patch__()
                ret.append(obj)
        return ret
    
    def count(self, **clause):
        controller = ~self
        url = '/api/node/class/' + self.class_name + '.json?'
        if len(clause) > 0:
            url += 'query-target-filter=and('
            for key in clause: url += 'eq(%s.%s,"%s"),' % (self.class_name, key, clause[key])
            url += ')&'
        url += 'rsp-subtree-include=count'
        try: data = controller.get(url)
        except Exception as e: raise ExceptAcidipyRetriveObject(controller, self.class_name, e)
        try: return int(data[0]['moCount']['attributes']['count'])
        except: raise ExceptAcidipyNonExistCount(controller, self.class_name)
    
    def health(self):
        controller = ~self
        url = '/api/node/class/' + self.class_name + '.json?&rsp-subtree-include=health'
        try: data = controller.get(url)
        except Exception as e: raise ExceptAcidipyRetriveObject(controller, self.class_name, e)
        ret = []
        for d in data:
            for class_name in d:
                attrs = d[class_name]['attributes']
                try:
                    for hinst_wrap in d[class_name]['children']:
                        if 'healthInst' in hinst_wrap:
                            hinst = hinst_wrap['healthInst']
                            ret.append({'dn' : attrs['dn'], 'score' : int(hinst['attributes']['cur'])})
                            break
                except: continue
        return ret
        
    def event(self, handler):
        controller = ~self
        handler.class_name = self.class_name
        if not controller.etrigger: controller.etrigger = Controller.EventTrigger(controller)
        controller.etrigger.register(handler)

#===============================================================================
# Actor Class
#===============================================================================
class AciActorClass:
     
    def __init__(self, parent, class_name, ident=None, prime_key=None):
        self.parent = parent
        self.controller = parent.controller
        self.class_name = class_name
        self.ident = ident
        self.prime_key = prime_key
        if class_name in PREPARE_CLASSES: self.prepare_class = globals()[PREPARE_CLASSES[class_name]]
        else: self.prepare_class = None
     
    def keys(self):
        if self.class_name in PREPARE_ATTRIBUTES: return PREPARE_ATTRIBUTES[self.class_name]
        url = '/api/class/' + self.class_name + '.json?page=0&page-size=1'
        try:
            data = self.controller.get(url)
            keys = sorted(data[0][self.class_name]['attributes'].keys())
        except Exception as e: raise ExceptAcidipyAttributes(self.controller, self.class_name, e)
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
        try: data = self.controller.get(url)
        except Exception as e: raise ExceptAcidipyRetriveObject(self.controller, self.class_name, e)
        ret = []
        for d in data:
            for class_name in d:
                obj = AciObject(**d[class_name]['attributes'])
                obj.class_name = class_name
                obj.controller = self.controller
                obj.is_detail = detail
                if self.prepare_class:
                    obj.__class__ = self.prepare_class
                    obj.__patch__()
                ret.append(obj)
        return ret
     
    def __call__(self, name, detail=False):
        dn = self.parent['dn'] + (self.ident % name)
        url = '/api/mo/' + dn + '.json'
        if not detail: url += '?rsp-prop-include=naming-only'
        try: data = self.controller.get(url)
        except Exception as e: raise ExceptAcidipyRetriveObject(self.controller, dn, e)
        for d in data:
            for class_name in d:
                obj = AciObject(**d[class_name]['attributes'])
                obj.controller = self.controller
                obj.class_name = class_name
                obj.is_detail = detail
                if self.prepare_class:
                    obj.__class__ = self.prepare_class
                    obj.__patch__()
                return obj
        raise ExceptAcidipyNonExistData(self.controller, dn)
     
    def count(self, **clause):
        url = '/api/node/class/' + self.class_name + '.json?query-target-filter=and(wcard(' + self.class_name + '.dn,"' + self.parent['dn'] + '/.*"),'
        if len(clause) > 0:
            for key in clause: url += 'eq(%s.%s,"%s"),' % (self.class_name, key, clause[key])
        url += ')&rsp-subtree-include=count'
        try: data = self.controller.get(url)
        except Exception as e: raise ExceptAcidipyRetriveObject(self.controller, self.class_name, e)
        try: return int(data[0]['moCount']['attributes']['count'])
        except: raise ExceptAcidipyNonExistCount(self.controller, self.class_name)
     
    def health(self):
        url = '/api/node/class/' + self.class_name + '.json?query-target-filter=wcard(' + self.class_name + '.dn,"' + self.parent['dn'] + '/.*")&rsp-subtree-include=health'
        try: data = self.controller.get(url)
        except Exception as e: raise ExceptAcidipyRetriveObject(self.controller, self.class_name, e)
        ret = []
        for d in data:
            for class_name in d:
                attrs = d[class_name]['attributes']
                try:
                    for hinst_wrap in d[class_name]['children']:
                        if 'healthInst' in hinst_wrap:
                            hinst = hinst_wrap['healthInst']
                            ret.append({'dn' : attrs['dn'], 'score' : int(hinst['attributes']['cur'])})
                            break
                except: continue
        return ret
     
    def event(self, handler):
        handler.class_name = self.class_name
        if self.controller.etrigger == None: self.controller.etrigger = Controller.EventTrigger(self.controller)
        self.controller.etrigger.register(handler)
         
    def create(self, **attributes):
        if self.prime_key == None or self.ident == None: raise ExceptAcidipyCreateObject(self.controller, self.class_name, ExceptAcidipyProcessing(self.controller, 'Uncompleted Identifier'))
        obj = AciObject(**attributes)
        obj.class_name = self.class_name
        try: ret = self.controller.post('/api/mo/' + self.parent['dn'] + '.json', obj.toJson())
        except Exception as e: raise ExceptAcidipyCreateObject(self.controller, self.class_name, e)
        if ret:
            obj.controller = self.controller
            obj['dn'] = self.parent['dn'] + (self.ident % attributes[self.prime_key])
            obj.is_detail = False
            if self.prepare_class:
                obj.__class__ = self.prepare_class
                obj.__patch__()
            return obj
        raise ExceptAcidipyCreateObject(self.controller, self.class_name, ExceptAcidipyProcessing(self.controller, 'Creation Failed'))
#===============================================================================
# Multi Domain Class
#===============================================================================
class AciMultiDomClass(Inventory):
     
    def __init__(self, actor_name):
        self.actor_name = actor_name        
     
    def list(self, detail=False, sort=None, page=None, **clause):
        multi_dom = ~self
        ret = {}; fetchs = []
        def fetch(multi_dom, dom_name, actor_name, detail, sort, page, clause, ret): ret[dom_name] = multi_dom[dom_name].__getattribute__(actor_name).list(detail, sort, page, **clause)
        for dom_name in multi_dom: fetchs.append(gevent.spawn(fetch, multi_dom, dom_name, self.actor_name, detail, sort, page, clause, ret))
        gevent.joinall(fetchs)
        return ret
     
    def health(self):
        multi_dom = ~self
        ret = {}; fetchs = []
        def fetch(multi_dom, dom_name, actor_name, ret): ret[dom_name] = multi_dom[dom_name].__getattribute__(actor_name).health() 
        for dom_name in multi_dom: fetchs.append(gevent.spawn(fetch, multi_dom, dom_name, self.actor_name, ret))
        gevent.joinall(fetchs)
        return ret
         
    def count(self, **clause):
        multi_dom = ~self
        ret = {}; fetchs = []
        def fetch(multi_dom, dom_name, actor_name, clause, ret): ret[dom_name] = multi_dom[dom_name].__getattribute__(actor_name).count(**clause)
        for dom_name in multi_dom: fetchs.append(gevent.spawn(fetch, multi_dom, dom_name, self.actor_name, clause, ret))
        gevent.joinall(fetchs)
        return ret

class AciMultiDomClassName(Inventory):
    
    def __init__(self, actor_name):
        self.actor_name = actor_name        
     
    def list(self, detail=False, sort=None, page=None, **clause):
        multi_dom = ~self
        ret = {}; fetchs = []
        def fetch(multi_dom, dom_name, actor_name, detail, sort, page, clause, ret): ret[dom_name] = multi_dom[dom_name].Class(actor_name).list(detail, sort, page, **clause)
        for dom_name in multi_dom: fetchs.append(gevent.spawn(fetch, multi_dom, dom_name, self.actor_name, detail, sort, page, clause, ret))
        gevent.joinall(fetchs)
        return ret
     
    def health(self):
        multi_dom = ~self
        ret = {}; fetchs = []
        def fetch(multi_dom, dom_name, actor_name, ret): ret[dom_name] = multi_dom[dom_name].Class(actor_name).health() 
        for dom_name in multi_dom: fetchs.append(gevent.spawn(fetch, multi_dom, dom_name, self.actor_name, ret))
        gevent.joinall(fetchs)
        return ret
         
    def count(self, **clause):
        multi_dom = ~self
        ret = {}; fetchs = []
        def fetch(multi_dom, dom_name, actor_name, clause, ret): ret[dom_name] = multi_dom[dom_name].Class(actor_name).count(**clause)
        for dom_name in multi_dom: fetchs.append(gevent.spawn(fetch, multi_dom, dom_name, self.actor_name, clause, ret))
        gevent.joinall(fetchs)
        return ret

#===============================================================================
# Object
#===============================================================================
class AciObject(dict):
    
    def __init__(self, **attributes):
        dict.__init__(self, **attributes)
        
    def __patch__(self): pass
    
    def toJson(self):
        data = {}
        data[self.class_name] = {'attributes' : self}
        return json.dumps(data, sort_keys=True)
    
    def keys(self):
        if self.class_name in PREPARE_ATTRIBUTES: return PREPARE_ATTRIBUTES[self.class_name]
        url = '/api/class/' + self.class_name + '.json?page=0&page-size=1'
        try:
            data = self.controller.get(url)
            keys = sorted(data[0][self.class_name]['attributes'].keys())
        except Exception as e: raise ExceptAcidipyAttributes(self.controller, self.class_name, e)
        if 'childAction' in keys: keys.remove('childAction')
        if 'dn' in keys: keys.remove('dn'); keys.insert(0, 'dn')
        if 'name' in keys: keys.remove('name'); keys.insert(0, 'name')
        if 'id' in keys: keys.remove('id'); keys.insert(0, 'id')
        PREPARE_ATTRIBUTES[self.class_name] = keys
        return keys
    
    def ident(self):
        dn = self['dn']
        if '/' not in dn: return None, self['dn'], None
        ret = re.match('(?P<path>.*)/(?P<ident>[a-zA-Z0-9]+)$', dn)
        if ret: return ret.group('path'), ret.group('ident'), None
        ret = re.match('(?P<path>.*)/(?P<ident>\w+)-\[?(?P<name>[\W\w]+)$', dn)
        if ret:
            name = ret.group('name')
            if ']' in name: name = name[:-1]
            return ret.group('path'), ret.group('ident'), name
        return None, None, None
    
    def dn(self):
        return self['dn']
    
    def rn(self):
        _, ident, name = self.ident()
        if not name: return ident
        return '%s-%s' % (ident, name)
    
    def name(self):
        if 'id' in self: return self['id']
        elif 'name' in self: return self['name']
        else: return self['dn']
    
    def path(self):
        return re.sub('/\w+-', '/', self['dn'])
    
    def detail(self):
        if not self.is_detail:
            url = '/api/mo/' + self['dn'] + '.json'
            try: data = self.controller.get(url)
            except Exception as e: raise ExceptAcidipyRetriveObject(self.controller, self['dn'], e)
            for d in data:
                for class_name in d:
                    attrs = d[class_name]['attributes']
                    for key in attrs: self[key] = attrs[key]
            self.is_detail = True
        return self

    def parent(self, detail=False):
        path, _, _ = self.ident()
        if not path: raise ExceptAcidipyNonExistParent(self.controller, self['dn'])
        url = '/api/mo/' + path + '.json'
        if not detail: url += '?rsp-prop-include=naming-only'
        try: data = self.controller.get(url)
        except Exception as e: raise ExceptAcidipyRetriveObject(self.controller, path, e)
        for d in data:
            for class_name in d:
                obj = AciObject(**d[class_name]['attributes'])
                obj.controller = self.controller
                obj.class_name = class_name
                obj.is_detail = detail
                if class_name in PREPARE_CLASSES:
                    obj.__class__ = globals()[PREPARE_CLASSES[class_name]]
                    obj.__patch__()
                return obj
        raise ExceptAcidipyNonExistData(self.controller, path)

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
        try: data = self.controller.get(url)
        except Exception as e: raise ExceptAcidipyRetriveObject(self.controller, self['dn'] + '/children', e)
        ret = []
        for d in data:
            for class_name in d:
                obj = AciObject(**d[class_name]['attributes'])
                obj.class_name = class_name
                obj.controller = self.controller
                obj.is_detail = detail
                if class_name in PREPARE_CLASSES:
                    obj.__class__ = globals()[PREPARE_CLASSES[class_name]]
                    obj.__patch__()
                ret.append(obj)
        return ret
    
    def Class(self, class_name, ident=None, prime_key=None):
        return AciActorClass(self, class_name, ident, prime_key)
    
    def health(self):
        url = '/api/mo/' + self['dn'] + '.json?rsp-subtree-include=health'
        try: data = self.controller.get(url)
        except Exception as e: raise ExceptAcidipyRetriveObject(self.controller, self['dn'], e)
        for d in data:
            for class_name in d:
                try:
                    for hinst_wrap in d[class_name]['children']:
                        if 'healthInst' in hinst_wrap:
                            hinst = hinst_wrap['healthInst']
                            return {'dn' : self['dn'], 'score' : int(hinst['attributes']['cur'])}
                except: continue
        raise ExceptAcidipyNonExistHealth(self.controller, self['dn'])
    
    def update(self):
        try: ret = self.controller.put('/api/mo/' + self['dn'] + '.json', data=self.toJson())
        except Exception as e: raise ExceptAcidipyUpdateObject(self.controller, self['dn'], e)
        if not ret: raise ExceptAcidipyUpdateObject(self.controller, self['dn'], ExceptAcidipyProcessing(self.controller, 'Updating Failed')) 
        return True
    
    def delete(self):
        try: ret = self.controller.delete('/api/mo/' + self['dn'] + '.json')
        except Exception as e: raise ExceptAcidipyDeleteObject(self.controller, self['dn'], e)
        if not ret: raise ExceptAcidipyDeleteObject(self.controller, self['dn'], ExceptAcidipyProcessing(self.controller, 'Deleting Failed'))
        return True

#  ________  ________ _________  ________  ________     
# |\   __  \|\   ____\\___   ___\\   __  \|\   __  \    
# \ \  \|\  \ \  \___\|___ \  \_\ \  \|\  \ \  \|\  \   
#  \ \   __  \ \  \       \ \  \ \ \  \\\  \ \   _  _\  
#   \ \  \ \  \ \  \____   \ \  \ \ \  \\\  \ \  \\  \| 
#    \ \__\ \__\ \_______\  \ \__\ \ \_______\ \__\\ _\ 
#     \|__|\|__|\|_______|   \|__|  \|_______|\|__|\|__|

class AciTenantActor(AciActorClass):
    def __init__(self, parent): AciActorClass.__init__(self, parent, 'fvTenant', '/tn-%s', 'name')
     
class AciFilterActor(AciActorClass):
    def __init__(self, parent): AciActorClass.__init__(self, parent, 'vzFilter', '/flt-%s', 'name')
 
class AciContractActor(AciActorClass):
    def __init__(self, parent): AciActorClass.__init__(self, parent, 'vzBrCP', '/brc-%s', 'name')
 
class AciContextActor(AciActorClass):
    def __init__(self, parent): AciActorClass.__init__(self, parent, 'fvCtx', '/ctx-%s', 'name')
     
class AciL3OutActor(AciActorClass):
    def __init__(self, parent): AciActorClass.__init__(self, parent, 'l3extOut', '/out-%s', 'name')
 
class AciL3ProfileActor(AciActorClass):
    def __init__(self, parent): AciActorClass.__init__(self, parent, 'l3extInstP', '/instP-%s', 'name')
     
class AciBridgeDomainActor(AciActorClass):
    def __init__(self, parent): AciActorClass.__init__(self, parent, 'fvBD', '/BD-%s', 'name')
 
class AciAppProfileActor(AciActorClass):
    def __init__(self, parent): AciActorClass.__init__(self, parent, 'fvAp', '/ap-%s', 'name')
 
class AciFilterEntryActor(AciActorClass):
    def __init__(self, parent): AciActorClass.__init__(self, parent, 'vzEntry', '/e-%s', 'name')
 
class AciSubjectActor(AciActorClass):
    def __init__(self, parent): AciActorClass.__init__(self, parent, 'vzSubj', '/subj-%s', 'name')
 
class AciSubnetActor(AciActorClass):
    def __init__(self, parent): AciActorClass.__init__(self, parent, 'fvSubnet', '/subnet-[%s]', 'ip')
 
class AciEPGActor(AciActorClass):
    def __init__(self, parent): AciActorClass.__init__(self, parent, 'fvAEPg', '/epg-%s', 'name')
 
class AciEndpointActor(AciActorClass):
    def __init__(self, parent): AciActorClass.__init__(self, parent, 'fvCEp', '/cep-%s', 'name')
 
class AciPodActor(AciActorClass):
    def __init__(self, parent): AciActorClass.__init__(self, parent, 'fabricPod', '/pod-%s', 'id')
     
    def health(self):
        url = '/api/node/class/fabricHealthTotal.json?query-target-filter=ne(fabricHealthTotal.dn,"topology/health")'
        try: data = self.controller.get(url)
        except Exception as e: raise ExceptAcidipyRetriveObject(self.controller, self.class_name, e)
        ret = []
        for d in data:
            for class_name in d:
                attrs = d[class_name]['attributes']
                if self.parent['dn'] in attrs['dn']:
                    obj = {'dn' : attrs['dn'].replace('/health', ''), 'score' : int(attrs['cur'])}
                    ret.append(obj)
        return ret
 
class AciNodeActor(AciActorClass):
    def __init__(self, parent): AciActorClass.__init__(self, parent, 'fabricNode', '/node-%s', 'id')
     
    def health(self):
        url = '/api/node/class/healthInst.json?query-target-filter=wcard(healthInst.dn,"^sys/health")'
        try: data = self.controller.get(url)
        except Exception as e: raise ExceptAcidipyRetriveObject(self.controller, self.class_name, e)
        ret = []
        for d in data:
            for class_name in d:
                attrs = d[class_name]['attributes']
                if self.parent['dn'] in attrs['dn']:
                    obj = {'dn' : attrs['dn'].replace('/sys/health', ''), 'score' : int(attrs['cur'])}
                    ret.append(obj)
        return ret
     
class AciPathsActor(AciActorClass):
    def __init__(self, parent): AciActorClass.__init__(self, parent, 'fabricPathEpCont', '/paths-%s', 'nodeId')
 
class AciVPathsActor(AciActorClass):
    def __init__(self, parent): AciActorClass.__init__(self, parent, 'fabricProtPathEpCont', '/protpaths-%s', 'nodeId')
 
class AciPathActor(AciActorClass):
    def __init__(self, parent): AciActorClass.__init__(self, parent, 'fabricPathEp', '/pathep-[%s]', 'name')
     
class AciPhysIfActor(AciActorClass):
    def __init__(self, parent): AciActorClass.__init__(self, parent, 'l1PhysIf', '/phys-[%s]', 'id')
     
    def health(self):
        url = '/api/node/class/healthInst.json?query-target-filter=wcard(healthInst.dn,"phys/health")'
        try: data = self.controller.get(url)
        except Exception as e: raise ExceptAcidipyRetriveObject(self.controller, self.class_name, e)
        ret = []
        for d in data:
            for class_name in d:
                attrs = d[class_name]['attributes']
                if self.parent['dn'] in attrs['dn']:
                    obj = {'dn' : attrs['dn'].replace('/phys/health', ''), 'score' : int(attrs['cur'])}
                    ret.append(obj)
        return ret


#  ________  ________        ___  _______   ________ _________   
# |\   __  \|\   __  \      |\  \|\  ___ \ |\   ____\\___   ___\ 
# \ \  \|\  \ \  \|\ /_     \ \  \ \   __/|\ \  \___\|___ \  \_| 
#  \ \  \\\  \ \   __  \  __ \ \  \ \  \_|/_\ \  \       \ \  \  
#   \ \  \\\  \ \  \|\  \|\  \\_\  \ \  \_|\ \ \  \____   \ \  \ 
#    \ \_______\ \_______\ \________\ \_______\ \_______\  \ \__\
#     \|_______|\|_______|\|________|\|_______|\|_______|   \|__|
#

class AciTenant(AciObject):
    
    @property
    def Filter(self): return AciFilterActor(self)
    
    @property
    def Contract(self): return AciContractActor(self)
    
    @property
    def Context(self): return AciContextActor(self)
    
    @property
    def L3Out(self): return AciL3OutActor(self)
    
    @property
    def BridgeDomain(self): return AciBridgeDomainActor(self)
    
    @property
    def AppProfile(self): return AciAppProfileActor(self)
    
class AciFilter(AciObject):
    
    @property
    def FilterEntry(self): return AciFilterEntryActor(self)

class AciContract(AciObject):
    
    @property
    def Subject(self): return AciSubjectActor(self)

class AciContext(AciObject): pass
     
class AciL3Out(AciObject):
    
    @property
    def L3Profile(self): return AciL3ProfileActor(self)
        
    def relate(self, obj, **attributes):
        if isinstance(obj, AciContext):
            attributes['tnFvCtxName'] = obj['name']
            try: ret = self.controller.post('/api/mo/' + self['dn'] + '.json', data=json.dumps({'l3extRsEctx' : {'attributes' : attributes}}))
            except Exception as e: raise ExceptAcidipyRelateObject(self.controller, self['dn'] + '<->' + obj['dn'], e)
            if ret: return True
        raise ExceptAcidipyRelateObject(self.controller, self['dn'] + '<->' + obj['dn'], ExceptAcidipyProcessing(self.controller, 'Relate Failed'))
    
class AciL3Profile(AciObject): pass

class AciBridgeDomain(AciObject):
    
    @property
    def Subnet(self): return AciSubnetActor(self)
        
    def relate(self, obj, **attributes):
        if isinstance(obj, AciContext):
            attributes['tnFvCtxName'] = obj['name']
            try: ret = self.controller.post('/api/mo/' + self['dn'] + '.json', data=json.dumps({'fvRsCtx' : {'attributes' : attributes}}))
            except Exception as e: raise ExceptAcidipyRelateObject(self.controller, self['dn'] + '<->' + obj['dn'], e)
            if ret: return True
        elif isinstance(obj, AciL3Out):
            attributes['tnL3extOutName'] = obj['name']
            try: ret = self.controller.post('/api/mo/' + self['dn'] + '.json', data=json.dumps({'fvRsBDToOut' : {'attributes' : attributes}}))
            except Exception as e: raise ExceptAcidipyRelateObject(self.controller, self['dn'] + '<->' + obj['dn'], e)
            if ret: return True
        raise ExceptAcidipyRelateObject(self.controller, self['dn'] + '<->' + obj['dn'], ExceptAcidipyProcessing(self.controller, 'Relate Failed'))
         
class AciAppProfile(AciObject):
    
    @property
    def EPG(self): return AciEPGActor(self)

class AciFilterEntry(AciObject): pass

class AciSubject(AciObject):
    
    def relate(self, obj, **attributes):
        if isinstance(obj, AciFilter):
            attributes['tnVzFilterName'] = obj['name']
            try: ret = self.controller.post('/api/mo/' + self['dn'] + '.json', data=json.dumps({'vzRsSubjFiltAtt' : {'attributes' : attributes}}))
            except Exception as e: raise ExceptAcidipyRelateObject(self.controller, self['dn'] + '<->' + obj['dn'], e)
            if ret: return True
        raise ExceptAcidipyRelateObject(self.controller, self['dn'] + '<->' + obj['dn'], ExceptAcidipyProcessing(self.controller, 'Relate Failed'))
         
class AciSubnet(AciObject): pass
     
class AciEPG(AciObject):
    
    @property
    def Endpoint(self): return AciEndpointActor(self)
    
    def relate(self, obj, **attributes):
        if isinstance(obj, AciBridgeDomain):
            attributes['tnFvBDName'] = obj['name']
            try: ret = self.controller.post('/api/mo/' + self['dn'] + '.json', data=json.dumps({'fvRsBd' : {'attributes' : attributes}}))
            except Exception as e: raise ExceptAcidipyRelateObject(self.controller, self['dn'] + '<->' + obj['dn'], e)
            if ret: return True
        elif isinstance(obj, AciContract):
            attributes['tnVzBrCPName'] = obj['name']
            try: ret = self.controller.post('/api/mo/' + self['dn'] + '.json', data=json.dumps({'fvRsProv' : {'attributes' : attributes}}))
            except Exception as e: raise ExceptAcidipyRelateObject(self.controller, self['dn'] + '<->' + obj['dn'], e)
            if ret: return True
        elif isinstance(obj, AciContract):
            attributes['tnVzBrCPName'] = obj['name']
            try: ret = self.controller.post('/api/mo/' + self['dn'] + '.json', data=json.dumps({'fvRsCons' : {'attributes' : attributes}}))
            except Exception as e: raise ExceptAcidipyRelateObject(self.controller, self['dn'] + '<->' + obj['dn'], e)
            if ret: return True
        elif isinstance(obj, AciPath): # need "encap" attribute
            attributes['tDn'] = obj['dn']
            try: ret = self.controller.post('/api/mo/' + self['dn'] + '.json', data=json.dumps({'fvRsPathAtt' : {'attributes' : attributes}}))
            except Exception as e: raise ExceptAcidipyRelateObject(self.controller, self['dn'] + '<->' + obj['dn'], e)
            if ret: return True
        raise ExceptAcidipyRelateObject(self.controller, self['dn'] + '<->' + obj['dn'], ExceptAcidipyProcessing(self.controller, 'Relate Failed'))
     
class AciEndpoint(AciObject): pass

class AciPod(AciObject):
    
    @property
    def Node(self): return AciNodeActor(self)
    
    @property
    def Paths(self): return AciPathsActor(self)
    
    @property
    def VPaths(self): return AciVPathsActor(self)

class AciNode(AciObject):
    
    def __patch__(self):
        if self.is_detail:
            if self['fabricSt'] == 'active' or self['role'] == 'controller':
                self.System = AciSystem(**self.controller(self['dn'] + '/sys', detail=self.is_detail))
                self.System.class_name = 'topSystem'
                self.System.controller = self.controller
                self.System.is_detail = self.is_detail
                self.System.__patch__()
        else:
            self.System = AciSystem(dn=self['dn'] + '/sys')
            self.System.class_name = 'topSystem'
            self.System.controller = self.controller
            self.System.is_detail = self.is_detail
            self.System.__patch__()

class AciSystem(AciObject):
    
    @property
    def PhysIf(self): return AciPhysIfActor(self)
        
class AciPaths(AciObject):
    
    @property
    def Path(self): return AciPathActor(self)
        
class AciVPaths(AciObject):
    
    @property
    def Path(self): return AciPathActor(self)

class AciPath(AciObject): pass

class AciPhysIf(AciObject): pass
        
#  ________  ________  ________   _________  ________  ________  ___       ___       _______   ________     
# |\   ____\|\   __  \|\   ___  \|\___   ___\\   __  \|\   __  \|\  \     |\  \     |\  ___ \ |\   __  \    
# \ \  \___|\ \  \|\  \ \  \\ \  \|___ \  \_\ \  \|\  \ \  \|\  \ \  \    \ \  \    \ \   __/|\ \  \|\  \   
#  \ \  \    \ \  \\\  \ \  \\ \  \   \ \  \ \ \   _  _\ \  \\\  \ \  \    \ \  \    \ \  \_|/_\ \   _  _\  
#   \ \  \____\ \  \\\  \ \  \\ \  \   \ \  \ \ \  \\  \\ \  \\\  \ \  \____\ \  \____\ \  \_|\ \ \  \\  \| 
#    \ \_______\ \_______\ \__\\ \__\   \ \__\ \ \__\\ _\\ \_______\ \_______\ \_______\ \_______\ \__\\ _\ 
#     \|_______|\|_______|\|__| \|__|    \|__|  \|__|\|__|\|_______|\|_______|\|_______|\|_______|\|__|\|__|
#                                                                                                           

class Event:
    
    #===========================================================================
    # Implementations
    #===========================================================================
    def handle(self, status, obj): pass

#===============================================================================
# Controller
#===============================================================================
class Controller(Session, AciObject):
    
    #===========================================================================
    # Inventory Classes
    #===========================================================================
    class Filter(AciGlobalClass):
        def __init__(self): AciGlobalClass.__init__(self, 'vzFilter')
    
    class Contract(AciGlobalClass):
        def __init__(self): AciGlobalClass.__init__(self, 'vzBrCP')
    
    class Context(AciGlobalClass):
        def __init__(self): AciGlobalClass.__init__(self, 'fvCtx')
    
    class L3Out(AciGlobalClass):
        def __init__(self): AciGlobalClass.__init__(self, 'l3extOut')
    
    class L3Profile(AciGlobalClass):
        def __init__(self): AciGlobalClass.__init__(self, 'l3extInstP')
        
    class BridgeDomain(AciGlobalClass):
        def __init__(self): AciGlobalClass.__init__(self, 'fvBD')
    
    class AppProfile(AciGlobalClass):
        def __init__(self): AciGlobalClass.__init__(self, 'fvAp')
    
    class FilterEntry(AciGlobalClass):
        def __init__(self): AciGlobalClass.__init__(self, 'vzEntry')
    
    class Subject(AciGlobalClass):
        def __init__(self): AciGlobalClass.__init__(self, 'vzSubj')
    
    class Subnet(AciGlobalClass):
        def __init__(self): AciGlobalClass.__init__(self, 'fvSubnet')
        
    class EPG(AciGlobalClass):
        def __init__(self): AciGlobalClass.__init__(self, 'fvAEPg')
    
    class Endpoint(AciGlobalClass):
        def __init__(self): AciGlobalClass.__init__(self, 'fvCEp')
        
    class Node(AciGlobalClass):
        def __init__(self): AciGlobalClass.__init__(self, 'fabricNode')
        
        def health(self):
            url = '/api/node/class/healthInst.json?query-target-filter=wcard(healthInst.dn,"^sys/health")'
            try: data = (~self).get(url)
            except Exception as e: raise ExceptAcidipyRetriveObject(~self, self.class_name, e)
            ret = []
            for d in data:
                for class_name in d:
                    attrs = d[class_name]['attributes']
                    obj = {'dn' : attrs['dn'].replace('/sys/health', ''), 'score' : int(attrs['cur'])}
                    ret.append(obj)
            return ret
    
    class Paths(AciGlobalClass):
        def __init__(self): AciGlobalClass.__init__(self, 'fabricPathEpCont')
    
    class VPaths(AciGlobalClass):
        def __init__(self): AciGlobalClass.__init__(self, 'fabricProtPathEpCont')
    
    class Path(AciGlobalClass):
        def __init__(self): AciGlobalClass.__init__(self, 'fabricPathEp')
    
    class System(AciGlobalClass):
        def __init__(self): AciGlobalClass.__init__(self, 'topSystem')
    
    class PhysIf(AciGlobalClass):
        def __init__(self): AciGlobalClass.__init__(self, 'l1PhysIf')
        
        def health(self):
            url = '/api/node/class/healthInst.json?query-target-filter=wcard(healthInst.dn,"phys/health")'
            try: data = (~self).get(url)
            except Exception as e: raise ExceptAcidipyRetriveObject(~self, self.class_name, e)
            ret = []
            for d in data:
                for class_name in d:
                    attrs = d[class_name]['attributes']
                    obj = {'dn' : attrs['dn'].replace('/phys/health', ''), 'score' : int(attrs['cur'])}
                    ret.append(obj)
            return ret
    
    class Fault(AciGlobalClass):
        def __init__(self): AciGlobalClass.__init__(self, 'faultInfo')
    
    #===========================================================================
    # EventTrigger
    #===========================================================================
    class EventTrigger:
    
        class Receiver(Task):
            
            def __init__(self, etrigger):
                Task.__init__(self)
                self.etrigger = etrigger
                self.start()
            
            def __run__(self):
                try: self.etrigger.__receive__()
                except Exception as e:
                    if self.etrigger.controller.debug: print('[Error]Aidipy:EventTrigger:Receiver>>%s' % str(e))
                    
        class Refresher(Task):
            
            def __init__(self, etrigger, refresh_sec):
                Task.__init__(self, refresh_sec, refresh_sec)
                self.etrigger = etrigger
                self.start()
            
            def __run__(self):
                try: self.etrigger.__refresh__()
                except Exception as e:
                    if self.etrigger.controller.debug: print('[Error]Acidipy:EventTrigger:Refresher>>%s' % str(e))
            
        def __init__(self, controller):
            self.controller = controller
            self.socket = None
            self.handlers = {}
            self.conn_status = True
            self.__connect__()
            self.receiver = Controller.EventTrigger.Receiver(self)
            self.refresher = Controller.EventTrigger.Refresher(self, ACIDIPY_SUBSCRIBER_REFRESH_SEC)
            
        def __connect__(self):
            if not self.conn_status: return
            if self.socket != None: self.socket.close()
            for _ in range(0, self.controller.retry):
                try: self.socket = create_connection('wss://%s/socket%s' % (self.controller.ip, self.controller.cookie), sslopt={'cert_reqs': ssl.CERT_NONE})
                except: continue
                if self.controller.debug: print('[Info]Acidipy:EventTrigger:Session:wss://%s/socket%s' % (self.controller.ip, self.controller.cookie))
                return
            raise ExceptAcidipyEventTriggerSession(self)
        
        def __refresh__(self):
            for subscribe_id in self.handlers:
                try: self.controller.get('/api/subscriptionRefresh.json?id=%s' % subscribe_id)
                except: continue
        
        def __receive__(self):
            try:
                data = json.loads(self.socket.recv())
                subscribe_ids = data['subscriptionId']
                if not isinstance(subscribe_ids, list): subscribe_ids = [subscribe_ids]
                subscribe_data = data['imdata']
            except: self.__connect__()
            else:
                for sd in subscribe_data:
                    for class_name in sd:
                        obj = AciObject(**sd[class_name]['attributes'])
                        obj.controller = self.controller
                        obj.class_name = class_name
                        obj.is_detail = True
                        if class_name in PREPARE_CLASSES:
                            obj.__class__ = globals()[PREPARE_CLASSES[class_name]]
                            obj.__patch__()
                        for subscribe_id in subscribe_ids:
                            try: self.handlers[subscribe_id].handle(obj['status'], obj)
                            except Exception as e:
                                if self.controller.debug: print('[Error]Acidipy:EventTrigger:Handler>>%s' % str(e))
        
        def close(self):
            self.conn_status = False
            self.refresher.stop()
            self.receiver.stop()
            self.socket.close()
        
        def register(self, handler):
            try: resp = self.controller.session.get(self.controller.url + '/api/class/%s.json?subscription=yes' % handler.class_name)
            except Exception as e: raise ExceptAcidipyEventTriggerRegister(self, e)
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    subscription_id = data['subscriptionId']
                    self.handlers[subscription_id] = handler
                    return subscription_id
                except Exception as e: raise ExceptAcidipyEventTriggerRegister(self, e)
            else: raise ExceptAcidipyEventTriggerRegister(self)
    
    def __init__(self, ip, usr, pwd, refresh_sec=ACIDIPY_REFRESH_SEC, **kargs):
        Session.__init__(self,
                         ip=ip,
                         usr=usr,
                         pwd=pwd,
                         refresh_sec=refresh_sec,
                         **kargs)
        AciObject.__init__(self,
                           ip=ip,
                           usr=usr,
                           pwd=pwd,
                           refresh_sec=refresh_sec,
                           **kargs)
        
        self.class_name = 'Controller'
        self.etrigger = None
        
        class RootDesc(dict):
            def __init__(self, controller, dn):
                dict.__init__(self, dn=dn)
                self.controller = controller
        
        self.Tenant = AciTenantActor(RootDesc(self, 'uni'))
        self.Pod = AciPodActor(RootDesc(self, 'topology'))
        
    def close(self):
        if self.etrigger != None: self.etrigger.close()
        Session.close(self)
                
    def detail(self): return self
    
    def health(self):
        url = '/api/node/class/fabricHealthTotal.json?query-target-filter=eq(fabricHealthTotal.dn,"topology/health")'
        try: data = self.get(url)
        except Exception as e: raise ExceptAcidipyRetriveObject(self, self.class_name, e)
        for d in data:
            for class_name in d:
                attrs = d[class_name]['attributes']
                return {'dn' : 'topology', 'score' : int(attrs['cur'])}
        raise ExceptAcidipyNonExistHealth(self, self.class_name)

    def Class(self, class_name):
        cls = AciGlobalClass(class_name)
        cls._inventory_root = self
        cls._inventory_parent = self
        cls._inventory_children = []
        return cls
    
    def __call__(self, dn, detail=False):
        url = '/api/mo/' + dn + '.json'
        if not detail: url += '?rsp-prop-include=naming-only'
        try: data = self.get(url)
        except Exception as e: raise ExceptAcidipyRetriveObject(self, dn, e)
        for d in data:
            for class_name in d:
                obj = AciObject(**d[class_name]['attributes'])
                obj.controller = self
                obj.class_name = class_name
                obj.is_detail = detail
                if class_name in PREPARE_CLASSES:
                    obj.__class__ = globals()[PREPARE_CLASSES[class_name]]
                    obj.__patch__()
                return obj
        raise ExceptAcidipyNonExistData(self, dn)

#===============================================================================
# Multi Domain
#===============================================================================
class MultiDomain(dict, Inventory):
    
    class Tenant(AciMultiDomClass):
        def __init__(self): AciMultiDomClass.__init__(self, 'Tenant')
    
    class Filter(AciMultiDomClass):
        def __init__(self): AciMultiDomClass.__init__(self, 'Filter')
    
    class Contract(AciMultiDomClass):
        def __init__(self): AciMultiDomClass.__init__(self, 'Contract')
    
    class Context(AciMultiDomClass):
        def __init__(self): AciMultiDomClass.__init__(self, 'Context')
    
    class L3Out(AciMultiDomClass):
        def __init__(self): AciMultiDomClass.__init__(self, 'L3Out')
    
    class L3Profile(AciMultiDomClass):
        def __init__(self): AciMultiDomClass.__init__(self, 'L3Profile')
    
    class BridgeDomain(AciMultiDomClass):
        def __init__(self): AciMultiDomClass.__init__(self, 'BridgeDomain')
    
    class AppProfile(AciMultiDomClass):
        def __init__(self): AciMultiDomClass.__init__(self, 'AppProfile')
    
    class FilterEntry(AciMultiDomClass):
        def __init__(self): AciMultiDomClass.__init__(self, 'FilterEntry')
    
    class Subject(AciMultiDomClass):
        def __init__(self): AciMultiDomClass.__init__(self, 'Subject')
    
    class Subnet(AciMultiDomClass):
        def __init__(self): AciMultiDomClass.__init__(self, 'Subnet')
    
    class EPG(AciMultiDomClass):
        def __init__(self): AciMultiDomClass.__init__(self, 'EPG')
    
    class Endpoint(AciMultiDomClass):
        def __init__(self): AciMultiDomClass.__init__(self, 'Endpoint')
    
    class Pod(AciMultiDomClass):
        def __init__(self): AciMultiDomClass.__init__(self, 'Pod')
    
    class Node(AciMultiDomClass):
        def __init__(self): AciMultiDomClass.__init__(self, 'Node')
    
    class Paths(AciMultiDomClass):
        def __init__(self): AciMultiDomClass.__init__(self, 'Paths')
    
    class VPaths(AciMultiDomClass):
        def __init__(self): AciMultiDomClass.__init__(self, 'VPaths')
    
    class Path(AciMultiDomClass):
        def __init__(self): AciMultiDomClass.__init__(self, 'Path')
    
    class System(AciMultiDomClass):
        def __init__(self): AciMultiDomClass.__init__(self, 'System')
    
    class PhysIf(AciMultiDomClass):
        def __init__(self): AciMultiDomClass.__init__(self, 'PhysIf')
    
    class Fault(AciMultiDomClass):
        def __init__(self): AciMultiDomClass.__init__(self, 'Fault')
    
    def __init__(self,
                 conns=Rest.DEFAULT_CONN_SIZE,
                 max_conns=Rest.DEFAULT_CONN_MAX,
                 retry=Rest.DEFAULT_CONN_RETRY,
                 refresh_sec=ACIDIPY_REFRESH_SEC,
                 debug=False):
        Inventory.__init__(self)
        dict.__init__(self)
        self.conns = conns
        self.max_conns = max_conns
        self.retry = retry
        self.refresh_sec = refresh_sec
        self.debug = debug
    
    def Class(self, class_name):
        cls = AciMultiDomClassName(class_name)
        cls._inventory_root = self
        cls._inventory_parent = self
        cls._inventory_children = []
        return cls
    
    def detail(self): return self
    
    def health(self):
        ret = {}; fetchs = []
        def fetch(multi_dom, dom_name, ret): ret[dom_name] = multi_dom[dom_name].health() 
        for dom_name in self: fetchs.append(gevent.spawn(fetch, self, dom_name, ret))
        gevent.joinall(fetchs)
        return ret
        
    def addDomain(self, domain_name, ip, usr, pwd):
        if domain_name in self:
            if self.debug: print('[Error]Acidipy:Multidomain:AddDomain:Already Exist Domain %s' % domain_name)
            return False
        opts = {'ip' : ip,
                'usr' : usr,
                'pwd' : pwd,
                'conns' : self.conns,
                'max_conns' : self.max_conns,
                'retry' : self.retry,
                'refresh_sec' : self.refresh_sec,
                'debug' : self.debug}
        try: ctrl = Controller(**opts)
        except Exception as e:
            if self.debug: print('[Error]Acidipy:Multidomain:AddDomain:%s' % str(e))
            return False
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
        
