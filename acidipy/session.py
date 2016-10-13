'''
Created on 2016. 10. 6.

@author: "comfact"
'''

import json
import requests
from .uni import *
from .topo import *
from .child import *

class ACISession:
    
    def __init__(self, ip, user, pwd, debug=False):
        try: requests.packages.urllib3.disable_warnings()
        except: pass
        self.debug = debug
        self.session = requests.Session()
        self.url = 'https://%s' % ip
        login_url = self.url + '/api/aaaLogin.json'
        data = {'aaaUser': {'attributes': {'name': user, 'pwd': pwd}}}
        resp = self.session.post(login_url, data=json.dumps(data, sort_keys=True), verify=False)
        if resp.status_code == 200: self.is_active = True
        else: self.is_active = False
        
    def close(self):
        self.session.close()
        
    #===========================================================================
    # Level 1 API
    #===========================================================================
    def get(self, url):
        if self.debug:
            print 'GET :', url
            resp = self.session.get(self.url + url)
            print 'CODE :', resp.status_code, '\n', resp.text, '\n'
        else:
            resp = self.session.get(self.url + url)
        if resp.status_code == 200: return resp.json()['imdata']
        return []
    
    def post(self, url, data):
        if self.debug:
            print 'POST :', url
            resp = self.session.post(self.url + url, data=data)
            print 'CODE :', resp.status_code, '\n', resp.text, '\n'
        else:
            resp = self.session.post(self.url + url, data=data)
        if resp.status_code == 200: return True
        return False
    
    def put(self, url, data):
        if self.debug:
            print 'PUT :', url
            resp = self.session.put(self.url + url, data=data)
            print 'CODE :', resp.status_code, '\n', resp.text, '\n'
        else:
            resp = self.session.put(self.url + url, data=data)
        if resp.status_code == 200: return True
        return False
    
    def delete(self, url):
        if self.debug:
            print 'DELETE :', url
            resp = self.session.delete(self.url + url)
            print 'CODE :', resp.status_code, '\n', resp.text, '\n'
        else:
            resp = self.session.delete(self.url + url)
        if resp.status_code == 200: return True
        return False
    
class Domain(ACISession):
    _OBJECT = 'Domain'
    _CHILD = [
              'fvTenant'
              ]
    
    ACI_OBJECT_MAPPING = {
        'fvTenant' : 'Tenant',
        'fvBD' : 'BridgeDomain',
        'fvSubnet' : 'Subnet',
        'fvAp' : 'AppProf',
        'fvAEPg' : 'EndPointGroup',
    }
    
    def __init__(self, ip, user, pwd, debug=False):
        ACISession.__init__(self, ip, user, pwd, debug)
        
    def __getObjCls__(self, obj_name):
        try: cls_name = Domain.ACI_OBJECT_MAPPING[obj_name]
        except: cls_name = 'ACIObject'
        try: return globals()[cls_name]
        except: return None
        
    def __lshift__(self, child):
        if child._OBJECT in self._CHILD: return child.create(self)
        return False
    
    #===========================================================================
    # Level 2 API
    #===========================================================================
    def getList(self, _target, _detail=False, **clause):
        query = '?'
        if not _detail: query += 'rsp-prop-include=naming-only&'
        if len(clause) > 0:
            query += 'query-target-filter=and('
            for key in clause: query += 'eq(%s.%s,"%s"),' % (_target, key, clause[key])
            query += ')'
        
        url = '/api/node/class/' + _target + '.json' + query
        data = self.get(url)
        ret = []
        for d in data:
            for obj_name in d:
                cls = self.__getObjCls__(obj_name)
                if cls: ret.append(cls(_object=obj_name, _domain=self, _detail=_detail, **d[obj_name]['attributes']))
        return ret
    
    def getHealthList(self, _target):
        ret = []
        if _target._HEALTH_TYPE == ACIObject.HEALTH_TYPE_CHILD:
            url = '/api/node/class/' + _target._OBJECT + '.json?rsp-subtree-include=health'
            data = self.get(url)
            for d in data:
                for obj_name in d:
                    dn = d[obj_name]['attributes']['dn']
                    prival = d[obj_name]['attributes'][_target._PRIKEY]
                    if 'children' in d[obj_name]: 
                        for c in d[obj_name]['children']:
                            if 'healthInst' in c:
                                health = Health(dn, c['healthInst']['attributes']['cur'])
                                health[_target._PRIKEY] = prival
                                ret.append(health)
                                break
        elif _target._HEALTH_TYPE == ACIObject.HEALTH_TYPE_URL:
            url = _target._HEALTH_URL
            data = self.get(url)
            for d in data:
                for obj_name in d:
                    attrs = d[obj_name]['attributes']
                    dn = _target._HEALTH_DNF(attrs['dn'])
                    health = Health(dn, attrs[_target._HEALTH_KEY])
                    health[_target._PRIKEY] = dn.split(_target._IDENTY)[1]
                    ret.append(health)
        return ret
    
    def getOne(self, _dn, _detail=False):
        url = '/api/mo/' + _dn + '.json'
        if not _detail: url += '?rsp-prop-include=naming-only'
        data = self.get(url)
        for d in data:
            for obj_name in d:
                cls = self.__getObjCls__(obj_name)
                if cls: return cls(_object=obj_name, _domain=self, _detail=_detail, **d[obj_name]['attributes'])
        return None
    
    def getChildren(self, _dn, _detail=False):
        url = '/api/mo/' + _dn + '.json?query-target=children'
        if not _detail: url += '&rsp-prop-include=naming-only'
        data = self.get(url)
        ret = []
        for d in data:
            for obj_name in d:
                cls = self.__getObjCls__(obj_name)
                if cls: ret.append(cls(_object=obj_name, _domain=self, _detail=_detail, **d[obj_name]['attributes']))
        return ret
    
    def create(self, _par_dn, _data):
        return self.post('/api/mo/' + _par_dn + '.json', _data)
    
    def update(self, _dn, _data):
        return self.put('/api/mo/' + _dn + '.json', _data)
    
    def delete(self, _dn):
        return ACISession.delete(self, '/api/mo/' + _dn + '.json')
