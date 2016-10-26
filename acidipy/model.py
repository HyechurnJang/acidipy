'''
Created on 2016. 10. 18.

@author: "comfact"
'''

import re
import json
from .session import Session
from .static import *

#===============================================================================
# Actor
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
                acidipy_obj.detail = detail
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
                acidipy_obj.detail = detail
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
    
    def health(self): raise AcidipyNonExistHealth(self.class_name)
    
    def create(self, **attributes): raise AcidipyCreateError(self.class_name)

#===============================================================================
# Uni Class Actor
#===============================================================================
class UniActor(AcidipyActor):
    
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
    
    def create(self, **attributes):
        acidipy_obj = AcidipyObject(**attributes)
        acidipy_obj.class_name = self.class_name
        if self.parent.domain.post('/api/mo/' + self.parent['dn'] + '.json', acidipy_obj.toJson()):
            acidipy_obj.domain = self.parent.domain
            acidipy_obj['dn'] = self.parent['dn'] + (self.class_ident % attributes[self.class_pkey])
            acidipy_obj.detail = False
            if self.prepare_class:
                acidipy_obj.__class__ = self.prepare_class
                acidipy_obj.__patch__()
            return acidipy_obj
        raise AcidipyCreateError(self.class_name)
    
class TenantActor(UniActor):
    def __init__(self, parent): UniActor.__init__(self, parent, 'fvTenant', 'name', '/tn-%s')
    
class ContractActor(UniActor):
    def __init__(self, parent): UniActor.__init__(self, parent, 'vzBrCP', 'name', '/brc-%s')
    def health(self): raise AcidipyNonExistHealth(self.class_name)

class VRFActor(UniActor):
    def __init__(self, parent): UniActor.__init__(self, parent, 'fvCtx', 'name', '/ctx-%s')
    
class BrDomActor(UniActor):
    def __init__(self, parent): UniActor.__init__(self, parent, 'fvBD', 'name', '/BD-%s')

class AppProfActor(UniActor):
    def __init__(self, parent): UniActor.__init__(self, parent, 'fvAp', 'name', '/ap-%s')

class SubnetActor(UniActor):
    def __init__(self, parent): UniActor.__init__(self, parent, 'fvSubnet', 'ip', '/subnet-[%s]')
    def health(self): raise AcidipyNonExistHealth(self.class_name)

class EPGActor(UniActor):
    def __init__(self, parent): UniActor.__init__(self, parent, 'fvAEPg', 'name', '/epg-%s')
    
class EPActor(UniActor):
    def __init__(self, parent): UniActor.__init__(self, parent, 'fvCEp', 'name', '/cep-%s')
    def health(self): raise AcidipyNonExistHealth(self.class_name)

#===============================================================================
# Topo Class Actor
#===============================================================================
class TopoActor(AcidipyActor): pass

class PodActor(TopoActor):
    def __init__(self, parent): TopoActor.__init__(self, parent, 'fabricPod', 'id', '/pod-%s')

class NodeActor(TopoActor):
    def __init__(self, parent): TopoActor.__init__(self, parent, 'fabricNode', 'id', '/node-%s')
    
class PathsActor(TopoActor):
    def __init__(self, parent): TopoActor.__init__(self, parent, 'fabricPathEpCont', 'nodeId', '/paths-%s')

class VPathsActor(TopoActor):
    def __init__(self, parent): TopoActor.__init__(self, parent, 'fabricProtPathEpCont', 'nodeId', '/protpaths-%s')

class PathActor(TopoActor):
    def __init__(self, parent): TopoActor.__init__(self, parent, 'fabricPathEp', 'name', '/pathep-[%s]')
    
#===============================================================================
# Abstraction
#===============================================================================
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
        if not self.detail:
            url = '/api/mo/' + self['dn'] + '.json'
            data = self.domain.get(url)
            for d in data:
                for class_name in d:
                    attrs = d[class_name]['attributes']
                    for key in attrs: self[key] = attrs[key]
            self.detail = True
        return self
    
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
                acidipy_obj.detail = detail
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
        data = self.domain.get(url)
        ret = []
        for d in data:
            for class_name in d:
                acidipy_obj = AcidipyObject(**d[class_name]['attributes'])
                acidipy_obj.class_name = class_name
                acidipy_obj.domain = self.domain
                acidipy_obj.detail = detail
                if class_name in PREPARE_CLASSES:
                    acidipy_obj.__class__ = globals()[PREPARE_CLASSES[class_name]]
                    acidipy_obj.__patch__()
                ret.append(acidipy_obj)
        return ret
    
    def health(self):
        raise AcidipyNonExistHealth(self['dn'])
    
    def update(self):
        raise AcidipyUpdateError(self['dn'])
    
    def delete(self):
        raise AcidipyDeleteError(self['dn'])

#===============================================================================
# Domain Model
#===============================================================================
class Domain(AcidipyObject):
    
    class ClassActor:
        
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
                    acidipy_obj.detail = detail
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
        
    class DomainActorDesc(dict):
        def __init__(self, domain, dn): dict.__init__(self, dn=dn); self.domain = domain
    
    def __init__(self, ip, user, pwd, debug=False):
        AcidipyObject.__init__(self, ip=ip, user=user, pwd=pwd, debug=debug)
        self.domain = Session(ip, user, pwd, debug)
        self.class_name = 'Domain'
        
        self.Tenant = TenantActor(Domain.DomainActorDesc(self.domain, 'uni'))
        
        self.Contract = Domain.ClassActor(self.domain, 'vzBrCP')
        self.VRF = Domain.ClassActor(self.domain, 'fvCtx')
        self.BrDom = Domain.ClassActor(self.domain, 'fvBD')
        self.AppProf = Domain.ClassActor(self.domain, 'fvAp')
        self.Subnet = Domain.ClassActor(self.domain, 'fvSubnet')
        self.EPG = Domain.ClassActor(self.domain, 'fvAEPg')
        self.EP = Domain.ClassActor(self.domain, 'fvCEp')
        
        self.Pod = PodActor(Domain.DomainActorDesc(self.domain, 'topology'))
        
        self.Node = Domain.ClassActor(self.domain, 'fabricNode')
        self.Paths = Domain.ClassActor(self.domain, 'fabricPathEpCont')
        self.VPaths = Domain.ClassActor(self.domain, 'fabricProtPathEpCont')
        self.Path = Domain.ClassActor(self.domain, 'fabricPathEp')

    def Class(self, class_name):
        return Domain.ClassActor(self.domain, class_name)
    
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
class UniObject(AcidipyObject):
    
    def update(self):
        if not self.domain.put('/api/mo/' + self['dn'] + '.json', data=self.toJson()): raise AcidipyUpdateError(self['dn'])
        return True
    
    def delete(self):
        if not self.domain.delete('/api/mo/' + self['dn'] + '.json'): raise AcidipyDeleteError(self['dn'])
        return True
        
class TenantObject(UniObject):
    
    def __patch__(self):
        self.Contract = ContractActor(self)
        self.VRF = VRFActor(self)
        self.BrDom = BrDomActor(self)
        self.AppProf = AppProfActor(self)
        
class ContractObject(UniObject): pass

class VRFObject(UniObject): pass
     
class BrDomObject(UniObject):
     
    def __patch__(self):
        self.Subnet = SubnetActor(self)
         
    def relate2VRF(self, vrf_object, **attributes):
        if isinstance(vrf_object, VRFObject):
            attributes['tnFvCtxName'] = vrf_object['name']
            if self.domain.post('/api/mo/' + self['dn'] + '.json', data=json.dumps({'fvRsCtx' : {'attributes' : attributes}})): return True
        raise AcidipyRelateError(self['dn'] + ' << >> ' + vrf_object['dn']) 
 
class AppProfObject(UniObject):
     
    def __patch__(self):
        self.EPG = EPGActor(self)
         
class SubnetObject(UniObject): pass
     
class EPGObject(UniObject):
    
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

class EPObject(UniObject): pass

#===============================================================================
# Topo Models
#===============================================================================
class TopoObject(AcidipyObject): pass
    
class PodObject(TopoObject):
    
    def __patch__(self):
        self.Node = NodeActor(self)
        self.Paths = PathsActor(self)
        self.VPaths = VPathsActor(self)

class NodeObject(TopoObject): pass

class PathsObject(TopoObject):
    
    def __patch__(self):
        self.Path = PathActor(self)
        
class VPathsObject(TopoObject):
    
    def __patch__(self):
        self.Path = PathActor(self)

class PathObject(TopoObject): pass
        








