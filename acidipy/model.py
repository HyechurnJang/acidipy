'''
Created on 2016. 10. 18.

@author: "comfact"
'''

import re
import ssl
import json
import gevent

from websocket import create_connection
from pygics import Task, RestAPI

from .static import *
from .session import Session

#######################################################################################################
#  ________  ___  ___  ________  ________  ________  ________  ___  ________  _______   ________      #
# |\   ____\|\  \|\  \|\   __  \|\   ____\|\   ____\|\   __  \|\  \|\   __  \|\  ___ \ |\   __  \     #
# \ \  \___|\ \  \\\  \ \  \|\ /\ \  \___|\ \  \___|\ \  \|\  \ \  \ \  \|\ /\ \   __/|\ \  \|\  \    #
#  \ \_____  \ \  \\\  \ \   __  \ \_____  \ \  \    \ \   _  _\ \  \ \   __  \ \  \_|/_\ \   _  _\   #
#   \|____|\  \ \  \\\  \ \  \|\  \|____|\  \ \  \____\ \  \\  \\ \  \ \  \|\  \ \  \_|\ \ \  \\  \|  #
#     ____\_\  \ \_______\ \_______\____\_\  \ \_______\ \__\\ _\\ \__\ \_______\ \_______\ \__\\ _\  #
#    |\_________\|_______|\|_______|\_________\|_______|\|__|\|__|\|__|\|_______|\|_______|\|__|\|__| #
#    \|_________|                  \|_________|                                                       #
#######################################################################################################

class SubscribeHandler:
    def subscribe(self, status, obj): pass

class Subscriber:
    
    #===========================================================================
    # Background Worker
    #===========================================================================
    class RefreshWork(Task):
        
        def __init__(self, subscriber, refresh_sec):
            Task.__init__(self, refresh_sec, refresh_sec)
            self.subscriber = subscriber
        
        def run(self):
            try: self.subscriber.__refresh__()
            except Exception as e:
                if self.subscriber.controller.debug: print('[Error]Acidipy:Subscriber:RefreshWork:%s' % str(e))
    
    class ReceiveWork(Task):
        
        def __init__(self, subscriber):
            Task.__init__(self)
            self.subscriber = subscriber
        
        def run(self):
            try: self.subscriber.__receive__()
            except Exception as e:
                if self.subscriber.controller.debug: print('[Error]Aidipy:Subscriber:ReceiveWork:%s' % str(e))
        
    #===========================================================================
    # Subscriber
    #===========================================================================
    def __init__(self, controller):
        self.controller = controller
        self.socket = None
        self.handlers = {}
        self.conn_status = True
        
        self.__connect__()
        
        self.receive_work = Subscriber.ReceiveWork(self).start()
        self.refresh_work = Subscriber.RefreshWork(self, ACIDIPY_SUBSCRIBER_REFRESH_SEC).start()
        
    def __connect__(self):
        if not self.conn_status: return
        if self.socket != None: self.socket.close()
        for _ in range(0, self.controller.retry):
            try: self.socket = create_connection('wss://%s/socket%s' % (self.controller.ip, self.controller.cookie), sslopt={'cert_reqs': ssl.CERT_NONE})
            except: continue
            if self.controller.debug: print('[Info]Acidipy:Subscriber:Session:wss://%s/socket%s' % (self.controller.ip, self.controller.cookie))
            return
        raise ExceptAcidipySubscriberSession(self)
    
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
                    acidipy_obj = ModelInterface(**sd[class_name]['attributes'])
                    acidipy_obj.controller = self.controller
                    acidipy_obj.class_name = class_name
                    acidipy_obj.is_detail = True
                    if class_name in PREPARE_CLASSES:
                        acidipy_obj.__class__ = globals()[PREPARE_CLASSES[class_name]]
                        acidipy_obj.__patch__()
                    for subscribe_id in subscribe_ids:
                        try: self.handlers[subscribe_id].subscribe(acidipy_obj['status'], acidipy_obj)
                        except Exception as e:
                            if self.controller.debug: print('[Error]Acidipy:Subscriber:Handler:%s' % str(e))
    
    def close(self):
        self.conn_status = False
        self.refresh_work.stop()
        self.receive_work.stop()
        self.socket.close()
    
    def register(self, handler):
        try: resp = self.controller.session.get(self.controller.url + '/api/class/%s.json?subscription=yes' % handler.class_name)
        except Exception as e: raise ExceptAcidipySubscriberRegister(self, e)
        if resp.status_code == 200:
            try:
                data = resp.json()
                subscription_id = data['subscriptionId']
                self.handlers[subscription_id] = handler
                return subscription_id
            except Exception as e: raise ExceptAcidipySubscriberRegister(self, e)
        else: raise ExceptAcidipySubscriberRegister(self)

##############################################################################################
#  ___  ________   _________  _______   ________  ________ ________  ________  _______       #
# |\  \|\   ___  \|\___   ___\\  ___ \ |\   __  \|\  _____\\   __  \|\   ____\|\  ___ \      #
# \ \  \ \  \\ \  \|___ \  \_\ \   __/|\ \  \|\  \ \  \__/\ \  \|\  \ \  \___|\ \   __/|     #
#  \ \  \ \  \\ \  \   \ \  \ \ \  \_|/_\ \   _  _\ \   __\\ \   __  \ \  \    \ \  \_|/__   #
#   \ \  \ \  \\ \  \   \ \  \ \ \  \_|\ \ \  \\  \\ \  \_| \ \  \ \  \ \  \____\ \  \_|\ \  #
#    \ \__\ \__\\ \__\   \ \__\ \ \_______\ \__\\ _\\ \__\   \ \__\ \__\ \_______\ \_______\ #
#     \|__|\|__| \|__|    \|__|  \|_______|\|__|\|__|\|__|    \|__|\|__|\|_______|\|_______| #
#                                                                                            #
##############################################################################################

class RootInterface:
    
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
        except: raise ExceptAcidipyAttributes()
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
        try: data = self.controller.get(url)
        except Exception as e: raise ExceptAcidipyRetriveObject(self.controller, self.class_name, e)
        ret = []
        for d in data:
            for class_name in d:
                acidipy_obj = ModelInterface(**d[class_name]['attributes'])
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
        try: data = self.controller.get(url)
        except Exception as e: raise ExceptAcidipyRetriveObject(self.controller, self.class_name, e)
        try: return int(data[0]['moCount']['attributes']['count'])
        except: raise ExceptAcidipyNonExistCount(self.controller, self.class_name)
    
    def health(self):
        url = '/api/node/class/' + self.class_name + '.json?&rsp-subtree-include=health'
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
                except Exception as e: print str(e); continue
        return ret
        
    def subscribe(self, handler):
        handler.class_name = self.class_name
        if self.controller.subscriber == None: self.controller.subscriber = Subscriber(self.controller)
        self.controller.subscriber.register(handler)

class PathInterface:
    
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
                acidipy_obj = ModelInterface(**d[class_name]['attributes'])
                acidipy_obj.class_name = class_name
                acidipy_obj.controller = self.controller
                acidipy_obj.is_detail = detail
                if self.prepare_class:
                    acidipy_obj.__class__ = self.prepare_class
                    acidipy_obj.__patch__()
                ret.append(acidipy_obj)
        return ret
    
    def __call__(self, rn, detail=False):
        dn = self.parent['dn'] + (self.class_ident % rn)
        url = '/api/mo/' + dn + '.json'
        if not detail: url += '?rsp-prop-include=naming-only'
        try: data = self.controller.get(url)
        except Exception as e: raise ExceptAcidipyRetriveObject(self.controller, dn, e)
        for d in data:
            for class_name in d:
                acidipy_obj = ModelInterface(**d[class_name]['attributes'])
                acidipy_obj.controller = self.controller
                acidipy_obj.class_name = class_name
                acidipy_obj.is_detail = detail
                if self.prepare_class:
                    acidipy_obj.__class__ = self.prepare_class
                    acidipy_obj.__patch__()
                return acidipy_obj
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
    
    def subscribe(self, handler):
        handler.class_name = self.class_name
        if self.controller.subscriber == None: self.controller.subscriber = Subscriber(self.controller)
        self.controller.subscriber.register(handler)
        
    def create(self, **attributes):
        if self.class_pkey == None or self.class_ident == None: raise ExceptAcidipyCreateObject(self.controller, self.class_name, ExceptAcidipyProcessing(self.controller, 'Uncompleted Identifier'))
        acidipy_obj = ModelInterface(**attributes)
        acidipy_obj.class_name = self.class_name
        try: ret = self.controller.post('/api/mo/' + self.parent['dn'] + '.json', acidipy_obj.toJson())
        except Exception as e: raise ExceptAcidipyCreateObject(self.controller, self.class_name, e)
        if ret:
            acidipy_obj.controller = self.controller
            acidipy_obj['dn'] = self.parent['dn'] + (self.class_ident % attributes[self.class_pkey])
            acidipy_obj.is_detail = False
            if self.prepare_class:
                acidipy_obj.__class__ = self.prepare_class
                acidipy_obj.__patch__()
            return acidipy_obj
        raise ExceptAcidipyCreateObject(self.controller, self.class_name, ExceptAcidipyProcessing(self.controller, 'Creation Failed'))

class MDRootInterface:
    
    def __init__(self, multi_dom, class_name):
        self.multi_dom = multi_dom
        self.class_name = class_name
        
    def list(self, detail=False, sort=None, page=None, **clause):
        ret = {}; fetchs = []
        def fetch(multi_dom, dom_name, class_name, detail, sort, page, clause, ret): ret[dom_name] = multi_dom[dom_name].Class(class_name).list(detail, sort, page, **clause)
        for dom_name in self.multi_dom: fetchs.append(gevent.spawn(fetch, self.multi_dom, dom_name, self.class_name, detail, sort, page, clause, ret))
        gevent.joinall(fetchs)
        return ret
    
    def count(self, **clause):
        ret = {}; fetchs = []
        def fetch(multi_dom, dom_name, class_name, clause, ret): ret[dom_name] = multi_dom[dom_name].Class(class_name).count(**clause)
        for dom_name in self.multi_dom: fetchs.append(gevent.spawn(fetch, self.multi_dom, dom_name, self.class_name, clause, ret))
        gevent.joinall(fetchs)
        return ret

class MDPathInterface:
    
    def __init__(self, multi_dom, actor_name):
        self.multi_dom = multi_dom
        self.actor_name = actor_name
    
    def list(self, detail=False, sort=None, page=None, **clause):
        ret = {}; fetchs = []
        def fetch(multi_dom, dom_name, actor_name, detail, sort, page, clause, ret): ret[dom_name] = multi_dom[dom_name].__getattribute__(actor_name).list(detail, sort, page, **clause) 
        for dom_name in self.multi_dom: fetchs.append(gevent.spawn(fetch, self.multi_dom, dom_name, self.actor_name, detail, sort, page, clause, ret))
        gevent.joinall(fetchs)
        return ret
    
    def health(self):
        ret = {}; fetchs = []
        def fetch(multi_dom, dom_name, actor_name, ret): ret[dom_name] = multi_dom[dom_name].__getattribute__(actor_name).health() 
        for dom_name in self.multi_dom: fetchs.append(gevent.spawn(fetch, self.multi_dom, dom_name, self.actor_name, ret))
        gevent.joinall(fetchs)
        return ret
        
    def count(self, **clause):
        ret = {}; fetchs = []
        def fetch(multi_dom, dom_name, actor_name, clause, ret): ret[dom_name] = multi_dom[dom_name].__getattribute__(actor_name).count(**clause)
        for dom_name in self.multi_dom: fetchs.append(gevent.spawn(fetch, self.multi_dom, dom_name, self.actor_name, clause, ret))
        gevent.joinall(fetchs)
        return ret

class ModelInterface(dict):
    
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
            try: data = self.controller.get(url)
            except Exception as e: raise ExceptAcidipyRetriveObject(self.controller, self['dn'], e)
            for d in data:
                for class_name in d:
                    attrs = d[class_name]['attributes']
                    for key in attrs: self[key] = attrs[key]
            self.is_detail = True
        return self

    def parent(self, detail=False):
        try: parent_dn = self['dn'].split(re.match('[\W\w]+(?P<rn>/\w+-\[?[\W\w]+]?)$', self['dn']).group('rn'))[0]
        except: raise ExceptAcidipyNonExistParent(self.controller, self['dn'])
        url = '/api/mo/' + parent_dn + '.json'
        if not detail: url += '?rsp-prop-include=naming-only'
        try: data = self.controller.get(url)
        except Exception as e: raise ExceptAcidipyRetriveObject(self.controller, parent_dn, e)
        for d in data:
            for class_name in d:
                acidipy_obj = ModelInterface(**d[class_name]['attributes'])
                acidipy_obj.controller = self.controller
                acidipy_obj.class_name = class_name
                acidipy_obj.is_detail = detail
                if class_name in PREPARE_CLASSES:
                    acidipy_obj.__class__ = globals()[PREPARE_CLASSES[class_name]]
                    acidipy_obj.__patch__()
                return acidipy_obj
        raise ExceptAcidipyNonExistData(self.controller, parent_dn)

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
                acidipy_obj = ModelInterface(**d[class_name]['attributes'])
                acidipy_obj.class_name = class_name
                acidipy_obj.controller = self.controller
                acidipy_obj.is_detail = detail
                if class_name in PREPARE_CLASSES:
                    acidipy_obj.__class__ = globals()[PREPARE_CLASSES[class_name]]
                    acidipy_obj.__patch__()
                ret.append(acidipy_obj)
        return ret
    
    def Class(self, class_name, class_pkey=None, class_ident=None):
        return PathInterface(self, class_name, class_pkey, class_ident)
    
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

##########################################################
#  ________  ________ _________  ________  ________      #
# |\   __  \|\   ____\\___   ___\\   __  \|\   __  \     #
# \ \  \|\  \ \  \___\|___ \  \_\ \  \|\  \ \  \|\  \    #
#  \ \   __  \ \  \       \ \  \ \ \  \\\  \ \   _  _\   #
#   \ \  \ \  \ \  \____   \ \  \ \ \  \\\  \ \  \\  \|  #
#    \ \__\ \__\ \_______\  \ \__\ \ \_______\ \__\\ _\  #
#     \|__|\|__|\|_______|   \|__|  \|_______|\|__|\|__| #
#                                                        #
##########################################################

class TenantActor(PathInterface):
    def __init__(self, parent): PathInterface.__init__(self, parent, 'fvTenant', 'name', '/tn-%s')
    
class FilterActor(PathInterface):
    def __init__(self, parent): PathInterface.__init__(self, parent, 'vzFilter', 'name', '/flt-%s')

class ContractActor(PathInterface):
    def __init__(self, parent): PathInterface.__init__(self, parent, 'vzBrCP', 'name', '/brc-%s')

class ContextActor(PathInterface):
    def __init__(self, parent): PathInterface.__init__(self, parent, 'fvCtx', 'name', '/ctx-%s')
    
class L3OutActor(PathInterface):
    def __init__(self, parent): PathInterface.__init__(self, parent, 'l3extOut', 'name', '/out-%s')

class L3ProfileActor(PathInterface):
    def __init__(self, parent): PathInterface.__init__(self, parent, 'l3extInstP', 'name', '/instP-%s')
    
class BridgeDomainActor(PathInterface):
    def __init__(self, parent): PathInterface.__init__(self, parent, 'fvBD', 'name', '/BD-%s')

class AppProfileActor(PathInterface):
    def __init__(self, parent): PathInterface.__init__(self, parent, 'fvAp', 'name', '/ap-%s')

class FilterEntryActor(PathInterface):
    def __init__(self, parent): PathInterface.__init__(self, parent, 'vzEntry', 'name', '/e-%s')

class SubjectActor(PathInterface):
    def __init__(self, parent): PathInterface.__init__(self, parent, 'vzSubj', 'name', '/subj-%s')

class SubnetActor(PathInterface):
    def __init__(self, parent): PathInterface.__init__(self, parent, 'fvSubnet', 'ip', '/subnet-[%s]')

class EPGActor(PathInterface):
    def __init__(self, parent): PathInterface.__init__(self, parent, 'fvAEPg', 'name', '/epg-%s')

class EndpointActor(PathInterface):
    def __init__(self, parent): PathInterface.__init__(self, parent, 'fvCEp', 'name', '/cep-%s')

class PodActor(PathInterface):
    def __init__(self, parent): PathInterface.__init__(self, parent, 'fabricPod', 'id', '/pod-%s')
    
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

class NodeActor(PathInterface):
    def __init__(self, parent): PathInterface.__init__(self, parent, 'fabricNode', 'id', '/node-%s')
    
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
    
class PathsActor(PathInterface):
    def __init__(self, parent): PathInterface.__init__(self, parent, 'fabricPathEpCont', 'nodeId', '/paths-%s')

class VPathsActor(PathInterface):
    def __init__(self, parent): PathInterface.__init__(self, parent, 'fabricProtPathEpCont', 'nodeId', '/protpaths-%s')

class PathActor(PathInterface):
    def __init__(self, parent): PathInterface.__init__(self, parent, 'fabricPathEp', 'name', '/pathep-[%s]')
    
class PhysIfActor(PathInterface):
    def __init__(self, parent): PathInterface.__init__(self, parent, 'l1PhysIf', 'id', '/phys-[%s]')
    
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


###############################################################
#  _____ ______   ________  ________  _______   ___           #
# |\   _ \  _   \|\   __  \|\   ___ \|\  ___ \ |\  \          #
# \ \  \\\__\ \  \ \  \|\  \ \  \_|\ \ \   __/|\ \  \         #
#  \ \  \\|__| \  \ \  \\\  \ \  \ \\ \ \  \_|/_\ \  \        #
#   \ \  \    \ \  \ \  \\\  \ \  \_\\ \ \  \_|\ \ \  \____   #
#    \ \__\    \ \__\ \_______\ \_______\ \_______\ \_______\ #
#     \|__|     \|__|\|_______|\|_______|\|_______|\|_______| #
#                                                             #
###############################################################

class aciTenantModel(ModelInterface):
    
    @property
    def Filter(self): return FilterActor(self)
    
    @property
    def Contract(self): return ContractActor(self)
    
    @property
    def Context(self): return ContextActor(self)
    
    @property
    def L3Out(self): return L3OutActor(self)
    
    @property
    def BridgeDomain(self): return BridgeDomainActor(self)
    
    @property
    def AppProfile(self): return AppProfileActor(self)
    
class aciFilterModel(ModelInterface):
    
    @property
    def FilterEntry(self): return FilterEntryActor(self)

class aciContractModel(ModelInterface):
    
    @property
    def Subject(self): return SubjectActor(self)

class aciContextModel(ModelInterface): pass
     
class aciL3OutModel(ModelInterface):
    
    @property
    def L3Profile(self): return L3ProfileActor(self)
        
    def relate(self, obj, **attributes):
        if isinstance(obj, aciContextModel):
            attributes['tnFvCtxName'] = obj['name']
            try: ret = self.controller.post('/api/mo/' + self['dn'] + '.json', data=json.dumps({'l3extRsEctx' : {'attributes' : attributes}}))
            except Exception as e: raise ExceptAcidipyRelateObject(self.controller, self['dn'] + '<->' + obj['dn'], e)
            if ret: return True
        raise ExceptAcidipyRelateObject(self.controller, self['dn'] + '<->' + obj['dn'], ExceptAcidipyProcessing(self.controller, 'Relate Failed'))
    
class aciL3ProfileModel(ModelInterface): pass

class aciBridgeDomainModel(ModelInterface):
    
    @property
    def Subnet(self): return SubnetActor(self)
        
    def relate(self, obj, **attributes):
        if isinstance(obj, aciContextModel):
            attributes['tnFvCtxName'] = obj['name']
            try: ret = self.controller.post('/api/mo/' + self['dn'] + '.json', data=json.dumps({'fvRsCtx' : {'attributes' : attributes}}))
            except Exception as e: raise ExceptAcidipyRelateObject(self.controller, self['dn'] + '<->' + obj['dn'], e)
            if ret: return True
        elif isinstance(obj, aciL3OutModel):
            attributes['tnL3extOutName'] = obj['name']
            try: ret = self.controller.post('/api/mo/' + self['dn'] + '.json', data=json.dumps({'fvRsBDToOut' : {'attributes' : attributes}}))
            except Exception as e: raise ExceptAcidipyRelateObject(self.controller, self['dn'] + '<->' + obj['dn'], e)
            if ret: return True
        raise ExceptAcidipyRelateObject(self.controller, self['dn'] + '<->' + obj['dn'], ExceptAcidipyProcessing(self.controller, 'Relate Failed'))
         
class aciAppProfileModel(ModelInterface):
    
    @property
    def EPG(self): return EPGActor(self)

class aciFilterEntryModel(ModelInterface): pass

class aciSubjectModel(ModelInterface):
    
    def relate(self, obj, **attributes):
        if isinstance(obj, aciFilterModel):
            attributes['tnVzFilterName'] = obj['name']
            try: ret = self.controller.post('/api/mo/' + self['dn'] + '.json', data=json.dumps({'vzRsSubjFiltAtt' : {'attributes' : attributes}}))
            except Exception as e: raise ExceptAcidipyRelateObject(self.controller, self['dn'] + '<->' + obj['dn'], e)
            if ret: return True
        raise ExceptAcidipyRelateObject(self.controller, self['dn'] + '<->' + obj['dn'], ExceptAcidipyProcessing(self.controller, 'Relate Failed'))
         
class aciSubnetModel(ModelInterface): pass
     
class aciEPGModel(ModelInterface):
    
    @property
    def Endpoint(self): return EndpointActor(self)
    
    def relate(self, obj, **attributes):
        if isinstance(obj, aciBridgeDomainModel):
            attributes['tnFvBDName'] = obj['name']
            try: ret = self.controller.post('/api/mo/' + self['dn'] + '.json', data=json.dumps({'fvRsBd' : {'attributes' : attributes}}))
            except Exception as e: raise ExceptAcidipyRelateObject(self.controller, self['dn'] + '<->' + obj['dn'], e)
            if ret: return True
        elif isinstance(obj, aciContractModel):
            attributes['tnVzBrCPName'] = obj['name']
            try: ret = self.controller.post('/api/mo/' + self['dn'] + '.json', data=json.dumps({'fvRsProv' : {'attributes' : attributes}}))
            except Exception as e: raise ExceptAcidipyRelateObject(self.controller, self['dn'] + '<->' + obj['dn'], e)
            if ret: return True
        elif isinstance(obj, aciContractModel):
            attributes['tnVzBrCPName'] = obj['name']
            try: ret = self.controller.post('/api/mo/' + self['dn'] + '.json', data=json.dumps({'fvRsCons' : {'attributes' : attributes}}))
            except Exception as e: raise ExceptAcidipyRelateObject(self.controller, self['dn'] + '<->' + obj['dn'], e)
            if ret: return True
        elif isinstance(obj, aciPathModel): # need "encap" attribute
            attributes['tDn'] = obj['dn']
            try: ret = self.controller.post('/api/mo/' + self['dn'] + '.json', data=json.dumps({'fvRsPathAtt' : {'attributes' : attributes}}))
            except Exception as e: raise ExceptAcidipyRelateObject(self.controller, self['dn'] + '<->' + obj['dn'], e)
            if ret: return True
        raise ExceptAcidipyRelateObject(self.controller, self['dn'] + '<->' + obj['dn'], ExceptAcidipyProcessing(self.controller, 'Relate Failed'))
     
class aciEndpointModel(ModelInterface): pass

class aciPodModel(ModelInterface):
    
    @property
    def Node(self): return NodeActor(self)
    
    @property
    def Paths(self): return PathsActor(self)
    
    @property
    def VPaths(self): return VPathsActor(self)

class aciNodeModel(ModelInterface):
    
    def __patch__(self):
        if self.is_detail:
            if self['fabricSt'] == 'active' or self['role'] == 'controller':
                self.System = aciSystemModel(**self.controller(self['dn'] + '/sys', detail=self.is_detail))
                self.System.class_name = 'topSystem'
                self.System.controller = self.controller
                self.System.is_detail = self.is_detail
                self.System.__patch__()
        else:
            self.System = aciSystemModel(dn=self['dn'] + '/sys')
            self.System.class_name = 'topSystem'
            self.System.controller = self.controller
            self.System.is_detail = self.is_detail
            self.System.__patch__()

class aciSystemModel(ModelInterface):
    
    @property
    def PhysIf(self): return PhysIfActor(self)
        
class aciPathsModel(ModelInterface):
    
    @property
    def Path(self): return PathActor(self)
        
class aciVPathsModel(ModelInterface):
    
    @property
    def Path(self): return PathActor(self)

class aciPathModel(ModelInterface): pass

class aciPhysIfModel(ModelInterface): pass
        
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
# Controller
#===============================================================================
class Controller(Session, ModelInterface):
    
    class FilterActor(RootInterface):
        def __init__(self, controller): RootInterface.__init__(self, controller, 'vzFilter')
    
    class ContractActor(RootInterface):
        def __init__(self, controller): RootInterface.__init__(self, controller, 'vzBrCP')
    
    class ContextActor(RootInterface):
        def __init__(self, controller): RootInterface.__init__(self, controller, 'fvCtx')
    
    class L3OutActor(RootInterface):
        def __init__(self, controller): RootInterface.__init__(self, controller, 'l3extOut')
    
    class L3ProfileActor(RootInterface):
        def __init__(self, controller): RootInterface.__init__(self, controller, 'l3extInstP')
        
    class BridgeDomainActor(RootInterface):
        def __init__(self, controller): RootInterface.__init__(self, controller, 'fvBD')
    
    class AppProfileActor(RootInterface):
        def __init__(self, controller): RootInterface.__init__(self, controller, 'fvAp')
    
    class FilterEntryActor(RootInterface):
        def __init__(self, controller): RootInterface.__init__(self, controller, 'vzEntry')
    
    class SubjectActor(RootInterface):
        def __init__(self, controller): RootInterface.__init__(self, controller, 'vzSubj')
    
    class SubnetActor(RootInterface):
        def __init__(self, controller): RootInterface.__init__(self, controller, 'fvSubnet')
    
    class EPGActor(RootInterface):
        def __init__(self, controller): RootInterface.__init__(self, controller, 'fvAEPg')
        
    class EndpointActor(RootInterface):
        def __init__(self, controller): RootInterface.__init__(self, controller, 'fvCEp')
        
    class NodeActor(RootInterface):
        def __init__(self, controller): RootInterface.__init__(self, controller, 'fabricNode')
        
        def health(self):
            url = '/api/node/class/healthInst.json?query-target-filter=wcard(healthInst.dn,"^sys/health")'
            try: data = self.controller.get(url)
            except Exception as e: raise ExceptAcidipyRetriveObject(self.controller, self.class_name, e)
            ret = []
            for d in data:
                for class_name in d:
                    attrs = d[class_name]['attributes']
                    obj = {'dn' : attrs['dn'].replace('/sys/health', ''), 'score' : int(attrs['cur'])}
                    ret.append(obj)
            return ret
    
    class PathsActor(RootInterface):
        def __init__(self, controller): RootInterface.__init__(self, controller, 'fabricPathEpCont')
    
    class VPathsActor(RootInterface):
        def __init__(self, controller): RootInterface.__init__(self, controller, 'fabricProtPathEpCont')
    
    class PathActor(RootInterface):
        def __init__(self, controller): RootInterface.__init__(self, controller, 'fabricPathEp')
    
    class SystemActor(RootInterface):
        def __init__(self, controller): RootInterface.__init__(self, controller, 'topSystem')
    
    class PhysIfActor(RootInterface):
        def __init__(self, controller): RootInterface.__init__(self, controller, 'l1PhysIf')
        
        def health(self):
            url = '/api/node/class/healthInst.json?query-target-filter=wcard(healthInst.dn,"phys/health")'
            try: data = self.controller.get(url)
            except Exception as e: raise ExceptAcidipyRetriveObject(self.controller, self.class_name, e)
            ret = []
            for d in data:
                for class_name in d:
                    attrs = d[class_name]['attributes']
                    obj = {'dn' : attrs['dn'].replace('/phys/health', ''), 'score' : int(attrs['cur'])}
                    ret.append(obj)
            return ret
    
    class FaultActor(RootInterface):
        def __init__(self, controller): RootInterface.__init__(self, controller, 'faultInfo')
    
    class ActorDesc(dict):
        def __init__(self, controller, dn): dict.__init__(self, dn=dn); self.controller = controller
    
    def __init__(self, ip, user, pwd, refresh_sec=ACIDIPY_REFRESH_SEC, **kargs):
        Session.__init__(self,
                         ip=ip,
                         user=user,
                         pwd=pwd,
                         refresh_sec=refresh_sec,
                         **kargs)
        ModelInterface.__init__(self,
                               ip=ip,
                               user=user,
                               pwd=pwd,
                               refresh_sec=refresh_sec,
                               **kargs)
        
        self.class_name = 'Controller'
        self.subscriber = None
        
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
        
    def close(self):
        if self.subscriber != None: self.subscriber.close()
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
        return RootInterface(self, class_name)
    
    def __call__(self, dn, detail=False):
        url = '/api/mo/' + dn + '.json'
        if not detail: url += '?rsp-prop-include=naming-only'
        try: data = self.get(url)
        except Exception as e: raise ExceptAcidipyRetriveObject(self, dn, e)
        for d in data:
            for class_name in d:
                acidipy_obj = ModelInterface(**d[class_name]['attributes'])
                acidipy_obj.controller = self
                acidipy_obj.class_name = class_name
                acidipy_obj.is_detail = detail
                if class_name in PREPARE_CLASSES:
                    acidipy_obj.__class__ = globals()[PREPARE_CLASSES[class_name]]
                    acidipy_obj.__patch__()
                return acidipy_obj
        raise ExceptAcidipyNonExistData(self, dn)

#===============================================================================
# Multi Domain
#===============================================================================

class MultiDomain(dict):
    
    def __init__(self,
                 conns=RestAPI.DEFAULT_CONN_SIZE,
                 conn_max=RestAPI.DEFAULT_CONN_MAX,
                 retry=RestAPI.DEFAULT_CONN_RETRY,
                 refresh_sec=ACIDIPY_REFRESH_SEC,
                 debug=False):
        dict.__init__(self)
        self.conns = conns
        self.conn_max = conn_max
        self.retry = retry
        self.refresh_sec = refresh_sec
        self.debug = debug
        
        self.Tenant = MDPathInterface(self, 'Tenant')
        self.Filter = MDPathInterface(self, 'Filter')
        self.Contract = MDPathInterface(self, 'Contract')
        self.Context = MDPathInterface(self, 'Context')
        self.L3Out = MDPathInterface(self, 'L3Out')
        self.L3Profile = MDPathInterface(self, 'L3Profile')
        self.BridgeDomain = MDPathInterface(self, 'BridgeDomain')
        self.AppProfile = MDPathInterface(self, 'AppProfile')
        self.FilterEntry = MDPathInterface(self, 'FilterEntry')
        self.Subject = MDPathInterface(self, 'Subject')
        self.Subnet = MDPathInterface(self, 'Subnet')
        self.EPG = MDPathInterface(self, 'EPG')
        self.Endpoint = MDPathInterface(self, 'Endpoint')
        
        self.Pod = MDPathInterface(self, 'Pod')
        
        self.Node = MDPathInterface(self, 'Node')
        self.Paths = MDPathInterface(self, 'Paths')
        self.VPaths = MDPathInterface(self, 'VPaths')
        self.Path = MDPathInterface(self, 'Path')
        self.System = MDPathInterface(self, 'System')
        self.PhysIf = MDPathInterface(self, 'PhysIf')
        
        self.Fault = MDPathInterface(self, 'Fault')
    
    def Class(self, class_name):
        return MDRootInterface(self, class_name)
    
    def detail(self): return self
    
    def health(self):
        ret = {}; fetchs = []
        def fetch(multi_dom, dom_name, ret): ret[dom_name] = multi_dom[dom_name].health() 
        for dom_name in self: fetchs.append(gevent.spawn(fetch, self, dom_name, ret))
        gevent.joinall(fetchs)
        return ret
        
    def addDomain(self, domain_name, ip, user, pwd):
        if domain_name in self:
            if self.debug: print('[Error]Acidipy:Multidomain:AddDomain:Already Exist Domain %s' % domain_name)
            return False
        opts = {'ip' : ip,
                'user' : user,
                'pwd' : pwd,
                'conns' : self.conns,
                'conn_max' : self.conn_max,
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
        
