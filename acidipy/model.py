'''
Created on 2016. 10. 18.

@author: "comfact"
'''

import re
import json
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
# Class Actor
#===============================================================================
class AcidipyActor:
    
    def __init__(self, parent, class_name, class_pkey=None, class_ident=None):
        self.parent = parent
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
        data = self.parent.domain.get(url)
        ret = []
        for d in data:
            for class_name in d:
                acidipy_obj = AcidipyObject(**d[class_name]['attributes'])
                acidipy_obj.class_name = class_name
                acidipy_obj.domain = self.parent.domain
                acidipy_obj.is_detail = detail
                if self.prepare_class:
                    acidipy_obj.__class__ = self.prepare_class
                    acidipy_obj.__patch__()
                ret.append(acidipy_obj)
        return ret
    
    def __call__(self, rn, detail=False):
        url = '/api/mo/' + self.parent['dn'] + (self.class_ident % rn) + '.json'
        if not detail: url += '?rsp-prop-include=naming-only'
        data = self.parent.domain.get(url)
        for d in data:
            for class_name in d:
                acidipy_obj = AcidipyObject(**d[class_name]['attributes'])
                acidipy_obj.domain = self.parent.domain
                acidipy_obj.class_name = class_name
                acidipy_obj.is_detail = detail
                if self.prepare_class:
                    acidipy_obj.__class__ = self.prepare_class
                    acidipy_obj.__patch__()
                return acidipy_obj
        raise AcidipyNonExistData(self.parent['dn'] + (self.class_ident % rn))
    
    def count(self):
        url = '/api/node/class/' + self.class_name + '.json?query-target-filter=wcard(' + self.class_name + '.dn,"' + self.parent['dn'] + '/.*")&rsp-subtree-include=count'
        data = self.parent.domain.get(url)
        try: return int(data[0]['moCount']['attributes']['count'])
        except: raise AcidipyNonExistCount(self.class_name)

class AcidipyActorHealth:

    def health(self):
        url = '/api/node/class/' + self.class_name + '.json?query-target-filter=wcard(' + self.class_name + '.dn,"' + self.parent['dn'] + '/.*")&rsp-subtree-include=health'
        data = self.parent.domain.get(url)
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
        if self.parent.domain.post('/api/mo/' + self.parent['dn'] + '.json', acidipy_obj.toJson()):
            acidipy_obj.domain = self.parent.domain
            acidipy_obj['dn'] = self.parent['dn'] + (self.class_ident % attributes[self.class_pkey])
            acidipy_obj.is_detail = False
            if self.prepare_class:
                acidipy_obj.__class__ = self.prepare_class
                acidipy_obj.__patch__()
            return acidipy_obj
        raise AcidipyCreateError(self.class_name)

class TenantActor(AcidipyActor, AcidipyActorHealth, AcidipyActorCreate):
    def __init__(self, parent): AcidipyActor.__init__(self, parent, 'fvTenant', 'name', '/tn-%s')
    
class ContractActor(AcidipyActor, AcidipyActorCreate):
    def __init__(self, parent): AcidipyActor.__init__(self, parent, 'vzBrCP', 'name', '/brc-%s')

class VRFActor(AcidipyActor, AcidipyActorHealth, AcidipyActorCreate):
    def __init__(self, parent): AcidipyActor.__init__(self, parent, 'fvCtx', 'name', '/ctx-%s')
    
class BrDomActor(AcidipyActor, AcidipyActorHealth, AcidipyActorCreate):
    def __init__(self, parent): AcidipyActor.__init__(self, parent, 'fvBD', 'name', '/BD-%s')

class AppProfActor(AcidipyActor, AcidipyActorHealth, AcidipyActorCreate):
    def __init__(self, parent): AcidipyActor.__init__(self, parent, 'fvAp', 'name', '/ap-%s')

class SubnetActor(AcidipyActor, AcidipyActorCreate):
    def __init__(self, parent): AcidipyActor.__init__(self, parent, 'fvSubnet', 'ip', '/subnet-[%s]')

class EPGActor(AcidipyActor, AcidipyActorHealth, AcidipyActorCreate):
    def __init__(self, parent): AcidipyActor.__init__(self, parent, 'fvAEPg', 'name', '/epg-%s')
    
class EPActor(AcidipyActor, AcidipyActorCreate):
    def __init__(self, parent): AcidipyActor.__init__(self, parent, 'fvCEp', 'name', '/cep-%s')

class PodActor(AcidipyActor):
    def __init__(self, parent): AcidipyActor.__init__(self, parent, 'fabricPod', 'id', '/pod-%s')

class NodeActor(AcidipyActor):
    def __init__(self, parent): AcidipyActor.__init__(self, parent, 'fabricNode', 'id', '/node-%s')
    
class PathsActor(AcidipyActor):
    def __init__(self, parent): AcidipyActor.__init__(self, parent, 'fabricPathEpCont', 'nodeId', '/paths-%s')

class VPathsActor(AcidipyActor):
    def __init__(self, parent): AcidipyActor.__init__(self, parent, 'fabricProtPathEpCont', 'nodeId', '/protpaths-%s')

class PathActor(AcidipyActor):
    def __init__(self, parent): AcidipyActor.__init__(self, parent, 'fabricPathEp', 'name', '/pathep-[%s]')

#===============================================================================
# Domain Actor
#===============================================================================
class DomainActor:
        
    def __init__(self, domain, class_name):
        self.domain = domain
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
        data = self.domain.get(url)
        ret = []
        for d in data:
            for class_name in d:
                acidipy_obj = AcidipyObject(**d[class_name]['attributes'])
                acidipy_obj.class_name = class_name
                acidipy_obj.domain = self.domain
                acidipy_obj.is_detail = detail
                if self.prepare_class:
                    acidipy_obj.__class__ = self.prepare_class
                    acidipy_obj.__patch__()
                ret.append(acidipy_obj)
        return ret
    
    def count(self):
        url = '/api/node/class/' + self.class_name + '.json?rsp-subtree-include=count'
        data = self.domain.get(url)
        try: return int(data[0]['moCount']['attributes']['count'])
        except: raise AcidipyNonExistCount(self.class_name)

class DomainActorHealth:
    
    def health(self):
        url = '/api/node/class/' + self.class_name + '.json?&rsp-subtree-include=health'
        data = self.domain.get(url)
        ret = []
        for d in data:
            for class_name in d:
                try: hinst = d[class_name]['children'][0]['healthInst']
                except: continue
                attrs = d[class_name]['attributes']
                obj = {'dn' : attrs['dn'], 'name' : attrs['name'], 'score' : int(hinst['attributes']['cur'])}
                ret.append(obj)
        return ret

class DomainContractActor(DomainActor):
    def __init__(self, domain): DomainActor.__init__(self, domain, 'vzBrCP')

class DomainVRFActor(DomainActor, DomainActorHealth):
    def __init__(self, domain): DomainActor.__init__(self, domain, 'fvCtx')
    
class DomainBrDomActor(DomainActor, DomainActorHealth):
    def __init__(self, domain): DomainActor.__init__(self, domain, 'fvBD')

class DomainAppProfActor(DomainActor, DomainActorHealth):
    def __init__(self, domain): DomainActor.__init__(self, domain, 'fvAp')

class DomainSubnetActor(DomainActor):
    def __init__(self, domain): DomainActor.__init__(self, domain, 'fvSubnet')

class DomainEPGActor(DomainActor, DomainActorHealth):
    def __init__(self, domain): DomainActor.__init__(self, domain, 'fvAEPg')
    
class DomainEPActor(DomainActor):
    def __init__(self, domain): DomainActor.__init__(self, domain, 'fvCEp')
    
class DomainNodeActor(DomainActor):
    def __init__(self, domain): DomainActor.__init__(self, domain, 'fabricNode')
    
class DomainPathsActor(DomainActor):
    def __init__(self, domain): DomainActor.__init__(self, domain, 'fabricPathEpCont')

class DomainVPathsActor(DomainActor):
    def __init__(self, domain): DomainActor.__init__(self, domain, 'fabricProtPathEpCont')

class DomainPathActor(DomainActor):
    def __init__(self, domain): DomainActor.__init__(self, domain, 'fabricPathEp')

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
            data = self.domain.get(url)
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
        data = self.domain.get(url)
        for d in data:
            for class_name in d:
                acidipy_obj = AcidipyObject(**d[class_name]['attributes'])
                acidipy_obj.domain = self.domain
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
        data = self.domain.get(url)
        ret = []
        for d in data:
            for class_name in d:
                acidipy_obj = AcidipyObject(**d[class_name]['attributes'])
                acidipy_obj.class_name = class_name
                acidipy_obj.domain = self.domain
                acidipy_obj.is_detail = detail
                if class_name in PREPARE_CLASSES:
                    acidipy_obj.__class__ = globals()[PREPARE_CLASSES[class_name]]
                    acidipy_obj.__patch__()
                ret.append(acidipy_obj)
        return ret

class AcidipyObjectHealth:
    
    def health(self):
        url = '/api/mo/' + self['dn'] + '.json?rsp-subtree-include=health'
        data = self.domain.get(url)
        for d in data:
            for class_name in d:
                try: hinst = d[class_name]['children'][0]['healthInst']
                except: continue
                return {'dn' : self['dn'], 'name' : self['name'], 'score' : int(hinst['attributes']['cur'])}
        raise AcidipyNonExistHealth(self['dn'])

class AcidipyObjectModify:
    
    def update(self):
        if not self.domain.put('/api/mo/' + self['dn'] + '.json', data=self.toJson()): raise AcidipyUpdateError(self['dn'])
        return True
    
    def delete(self):
        if not self.domain.delete('/api/mo/' + self['dn'] + '.json'): raise AcidipyDeleteError(self['dn'])
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
# Domain Model
#===============================================================================
class Domain(AcidipyObject):
    
    class DomainActorDesc(dict):
        def __init__(self, domain, dn): dict.__init__(self, dn=dn); self.domain = domain
    
    def __init__(self, ip, user, pwd, debug=False):
        AcidipyObject.__init__(self, ip=ip, user=user, pwd=pwd, debug=debug)
        self.domain = Session(ip, user, pwd, debug)
        self.class_name = 'Domain'
        
        self.Tenant = TenantActor(Domain.DomainActorDesc(self.domain, 'uni'))
        
        self.Contract = DomainContractActor(self.domain)
        self.VRF = DomainVRFActor(self.domain)
        self.BrDom = DomainBrDomActor(self.domain)
        self.AppProf = DomainAppProfActor(self.domain)
        self.Subnet = DomainSubnetActor(self.domain)
        self.EPG = DomainEPGActor(self.domain)
        self.EP = DomainEPActor(self.domain)
        
        self.Pod = PodActor(Domain.DomainActorDesc(self.domain, 'topology'))
        
        self.Node = DomainNodeActor(self.domain)
        self.Paths = DomainPathsActor(self.domain)
        self.VPaths = DomainVPathsActor(self.domain)
        self.Path = DomainPathActor(self.domain)
        
    def detail(self): return self

    def Class(self, class_name):
        return DomainActor(self.domain, class_name)
    
    def __call__(self, dn, detail=False):
        url = '/api/mo/' + dn + '.json'
        if not detail: url += '?rsp-prop-include=naming-only'
        data = self.domain.get(url)
        for d in data:
            for class_name in d:
                acidipy_obj = AcidipyObject(**d[class_name]['attributes'])
                acidipy_obj.domain = self.domain
                acidipy_obj.class_name = class_name
                acidipy_obj.detail = detail
                if class_name in PREPARE_CLASSES:
                    acidipy_obj.__class__ = globals()[PREPARE_CLASSES[class_name]]
                    acidipy_obj.__patch__()
                return acidipy_obj
        raise AcidipyNonExistData(dn)
    
    def close(self):
        self.domain.close()

#===============================================================================
# Uni Models
#===============================================================================
class TenantObject(AcidipyObject, AcidipyObjectChildren, AcidipyObjectHealth, AcidipyObjectModify):
    
    def __patch__(self):
        self.Contract = ContractActor(self)
        self.VRF = VRFActor(self)
        self.BrDom = BrDomActor(self)
        self.AppProf = AppProfActor(self)
        
class ContractObject(AcidipyObject, AcidipyObjectParent, AcidipyObjectChildren, AcidipyObjectModify): pass

class VRFObject(AcidipyObject, AcidipyObjectParent, AcidipyObjectChildren, AcidipyObjectHealth, AcidipyObjectModify): pass
     
class BrDomObject(AcidipyObject, AcidipyObjectParent, AcidipyObjectChildren, AcidipyObjectHealth, AcidipyObjectModify):
     
    def __patch__(self):
        self.Subnet = SubnetActor(self)
         
    def relate2VRF(self, vrf_object, **attributes):
        if isinstance(vrf_object, VRFObject):
            attributes['tnFvCtxName'] = vrf_object['name']
            if self.domain.post('/api/mo/' + self['dn'] + '.json', data=json.dumps({'fvRsCtx' : {'attributes' : attributes}})): return True
        raise AcidipyRelateError(self['dn'] + ' << >> ' + vrf_object['dn']) 
 
class AppProfObject(AcidipyObject, AcidipyObjectParent, AcidipyObjectChildren, AcidipyObjectHealth, AcidipyObjectModify):
     
    def __patch__(self):
        self.EPG = EPGActor(self)
         
class SubnetObject(AcidipyObject, AcidipyObjectParent, AcidipyObjectChildren, AcidipyObjectModify): pass
     
class EPGObject(AcidipyObject, AcidipyObjectParent, AcidipyObjectChildren, AcidipyObjectHealth, AcidipyObjectModify):
    
    def __patch__(self):
        self.EP = EPActor(self)
     
    def relate2BrDom(self, bd_object, **attributes):
        if isinstance(bd_object, BrDomObject):
            attributes['tnFvBDName'] = bd_object['name']
            if self.domain.post('/api/mo/' + self['dn'] + '.json', data=json.dumps({'fvRsBd' : {'attributes' : attributes}})): return True
        raise AcidipyRelateError(self['dn'] + ' << >> ' + bd_object['dn'])
    
    def relate2Provider(self, ctr_object, **attributes):
        if isinstance(ctr_object, ContractObject):
            attributes['tnVzBrCPName'] = ctr_object['name']
            if self.domain.post('/api/mo/' + self['dn'] + '.json', data=json.dumps({'fvRsProv' : {'attributes' : attributes}})): return True
        raise AcidipyRelateError(self['dn'] + ' << >> ' + ctr_object['dn'])
    
    def relate2Consumer(self, ctr_object, **attributes):
        if isinstance(ctr_object, ContractObject):
            attributes['tnVzBrCPName'] = ctr_object['name']
            if self.domain.post('/api/mo/' + self['dn'] + '.json', data=json.dumps({'fvRsCons' : {'attributes' : attributes}})): return True
        raise AcidipyRelateError(self['dn'] + ' << >> ' + ctr_object['dn'])
    
    def relate2StaticPath(self, path_object, encap, **attributes):
        if isinstance(path_object, PathObject):
            attributes['tDn'] = path_object['dn']
            attributes['encap'] = encap
            if self.domain.post('/api/mo/' + self['dn'] + '.json', data=json.dumps({'fvRsPathAtt' : {'attributes' : attributes}})): return True
        raise AcidipyRelateError(self['dn'] + ' << >> ' + path_object['dn'])

class EPObject(AcidipyObject, AcidipyObjectParent): pass

#===============================================================================
# Topo Models
#===============================================================================
class PodObject(AcidipyObject, AcidipyObjectChildren):
    
    def __patch__(self):
        self.Node = NodeActor(self)
        self.Paths = PathsActor(self)
        self.VPaths = VPathsActor(self)

class NodeObject(AcidipyObject, AcidipyObjectParent, AcidipyObjectChildren): pass

class PathsObject(AcidipyObject, AcidipyObjectParent, AcidipyObjectChildren):
    
    def __patch__(self):
        self.Path = PathActor(self)
        
class VPathsObject(AcidipyObject, AcidipyObjectParent, AcidipyObjectChildren):
    
    def __patch__(self):
        self.Path = PathActor(self)

class PathObject(AcidipyObject, AcidipyObjectParent): pass
        








