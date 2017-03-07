'''
Created on 2016. 10. 6.

@author: "comfact"
'''

from pygics import RestAPI
from .static import *

class Session(RestAPI):
    
    def __init__(self, ip, user, pwd, **kargs):
        RestAPI.__init__(self, ip, user, pwd, proto=RestAPI.PROTO_HTTPS, **kargs)
    
    def __login__(self, req):
        try: resp = req.post(self.url + '/api/aaaLogin.json',
                             json={'aaaUser': {'attributes': {'name': self.user, 'pwd': self.pwd}}},
                             verify=False, timeout=2.0)
        except: raise ExceptAcidipySession(self)
        if resp.status_code == 200:
            self.cookie = resp.cookies['APIC-cookie']
            if self.debug: print('APIC Session Connect to %s with %s' % (self.url, self.cookie))
            return 'APIC-cookie=%s' % self.cookie
        raise ExceptAcidipySession(self)
    
    def __refresh__(self, req):
        try: resp = req.get(self.url + '/api/aaaRefresh.json',
                            cookies=self.__cookie__(),
                            verify=False, timeout=2.0)
        except: raise ExceptAcidipySession(self)
        if resp.status_code == 200:
            self.cookie = resp.cookies['APIC-cookie']
            if self.debug: print('APIC Session Refresh to %s with %s' % (self.url, self.cookie))
            return 'APIC-cookie=%s' % self.cookie
        raise ExceptAcidipySession(self)
    
    def __cookie__(self): return {'Set-Cookie' : self.token}
    
    def get(self, url):
        for i in range(0, self.retry):
            resp = RestAPI.get(self, url)
            if resp.status_code == 200: return resp.json()['imdata']
            elif resp.status_code == 403: self.refresh()
            else:
                try:
                    error = resp.json()['imdata'][0]['error']['attributes']
                    code = error['code']; text = error['text']
                except: raise ExceptAcidipyResponse(self, resp.status_code, url)
                else: raise ExceptAcidipyResponse(self, code, text)
        raise ExceptAcidipySession(self)
    
    def post(self, url, data):
        for i in range(0, self.retry):
            resp = RestAPI.post(self, url, data)
            if resp.status_code == 200: return True
            elif resp.status_code == 403: self.refresh()
            else:
                try:
                    error = resp.json()['imdata'][0]['error']['attributes']
                    code = error['code']; text = error['text']
                except: raise ExceptAcidipyResponse(self, resp.status_code, url)
                else: raise ExceptAcidipyResponse(self, code, text)
        raise ExceptAcidipySession(self)
    
    def put(self, url, data):
        for i in range(0, self.retry):
            resp = RestAPI.put(self, url, data)
            if resp.status_code == 200: return True
            elif resp.status_code == 403: self.refresh()
            else:
                try:
                    error = resp.json()['imdata'][0]['error']['attributes']
                    code = error['code']; text = error['text']
                except: raise ExceptAcidipyResponse(self, resp.status_code, url)
                else: raise ExceptAcidipyResponse(self, code, text)
        raise ExceptAcidipySession(self)
    
    def delete(self, url):
        for i in range(0, self.retry):
            resp = RestAPI.delete(self, url)
            if resp.status_code == 200: return True
            elif resp.status_code == 403: self.refresh()
            else:
                try:
                    error = resp.json()['imdata'][0]['error']['attributes']
                    code = error['code']; text = error['text']
                except: raise ExceptAcidipyResponse(self, resp.status_code, url)
                else: raise ExceptAcidipyResponse(self, code, text)
        raise ExceptAcidipySession(self)
