'''
Created on 2016. 10. 6.

@author: "comfact"
'''

import json
import string

from pygics import Rest
from .static import *

class Session(Rest):
    
    def __init__(self, ip, usr, pwd, **kargs):
        Rest.__init__(self, 'https://' + ip, usr, pwd, **kargs)
        self.ip = ip
    
    def __login__(self, session):
        try: resp = session.post(self.url + '/api/aaaLogin.json',
                                 json={'aaaUser': {'attributes': {'name': self.usr, 'pwd': self.pwd}}},
                                 verify=False, timeout=2.0)
        except: raise ExceptAcidipySession(self)
        if resp.status_code == 200:
            self.cookie = resp.cookies['APIC-cookie']
            if self.debug: print('APIC Session Connect to %s with %s' % (self.url, self.cookie))
            return 'APIC-cookie=%s' % self.cookie
        raise ExceptAcidipySession(self)
    
    def __refresh__(self, session):
        try: resp = session.get(self.url + '/api/aaaRefresh.json',
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
        for _ in range(0, self.retry):
            resp = Rest.get(self, url)
            if resp.status_code == 200:
                try: return resp.json()['imdata']
                except Exception as e:
                    try: return json.loads(''.join(x for x in resp.text if x in string.printable))['imdata']
                    except: raise ExceptAcidipyResponse(self, resp.status_code, str(e))
            elif resp.status_code == 403: self.refresh()
            else:
                try:
                    error = resp.json()['imdata'][0]['error']['attributes']
                    code = error['code']; text = error['text']
                except: raise ExceptAcidipyResponse(self, resp.status_code, url)
                else: raise ExceptAcidipyResponse(self, code, text)
        raise ExceptAcidipySession(self)
    
    def post(self, url, data):
        for _ in range(0, self.retry):
            resp = Rest.post(self, url, data)
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
        for _ in range(0, self.retry):
            resp = Rest.put(self, url, data)
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
        for _ in range(0, self.retry):
            resp = Rest.delete(self, url)
            if resp.status_code == 200: return True
            elif resp.status_code == 403: self.refresh()
            else:
                try:
                    error = resp.json()['imdata'][0]['error']['attributes']
                    code = error['code']; text = error['text']
                except: raise ExceptAcidipyResponse(self, resp.status_code, url)
                else: raise ExceptAcidipyResponse(self, code, text)
        raise ExceptAcidipySession(self)
