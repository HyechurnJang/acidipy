'''
Created on 2016. 10. 6.

@author: "comfact"
'''

import json
import requests

class ACISession:
    
    def __init__(self, ip, user, pwd):
        try: requests.packages.urllib3.disable_warnings()
        except: pass
        self.session = requests.Session()
        self.url = 'https://%s' % ip
        login_url = self.url + '/api/aaaLogin.json'
        data = {'aaaUser': {'attributes': {'name': user, 'pwd': pwd}}}
        self.session.post(login_url, data=json.dumps(data, sort_keys=True), verify=False)
        
    def close(self):
        self.session.close()
        
    #===========================================================================
    # Level 1 Rest Call
    #===========================================================================
    def get(self, url):
        resp = self.session.get(self.url + url)
        if resp.status_code == 200: return resp.json()['imdata']
        return []
    
    def post(self, url, data):
        resp = self.session.post(self.url + url, data=data)
        if resp.status_code == 200: return True
        return False
    
    def put(self, url, data):
        resp = self.session.put(self.url + url, data=data)
        if resp.status_code == 200: return True
        return False
    
    def delete(self, url):
        resp = self.session.delete(self.url + url)
        if resp.status_code == 200: return True
        return False
    
class Domain(ACISession):
    
    ACI_OBJECT_MAPPING = {
        'fvTenant' : 'Tenant',
        'fvBD' : 'BridgeDomain',
        'fvAp' : 'AppProf',
        'fvAEPg' : 'EndPointGroup',
    }
    
    def __init__(self, ip, user, pwd):
        ACISession.__init__(self, ip, user, pwd)
        
    def __getObjCls__(self, obj_name):
        try: cls_name = Domain.ACI_OBJECT_MAPPING[obj_name]
        except: cls_name = 'ACIObject'
        try: return globals()[cls_name]
        except: return None
    
    #===========================================================================
    # Level 2 Rest Call
    #===========================================================================
    def getList(self, _target, _detail=False, **clause):
        query = '?'
        if not _detail: query += 'rsp-prop-include=naming-only&'
        if len(clause) > 0:
            query += 'query-target-filter=and('
            for key in clause: query += 'eq(%s.%s,"%s"),' % (_target, key, clause[key])
            query += ')'
        
        url = '/api/node/class/' + _target +'.json' + query
        data = self.get(url)
        ret = []
        for d in data:
            for obj_name in d:
                cls = self.__getObjCls__(obj_name)
                if cls: ret.append(cls(_object=obj_name, _domain=self, _detail=_detail, **d[obj_name]['attributes']))
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
    
    def create(self, _par_dn, _data):
        return self.post('/api/mo/' + _par_dn + '.json', _data)
    
    def update(self, _dn, _data):
        return self.put('/api/mo/' + _dn + '.json', _data)
    
    def delete(self, _dn):
        return ACISession.delete(self, '/api/mo/' + _dn + '.json')
