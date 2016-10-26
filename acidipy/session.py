'''
Created on 2016. 10. 6.

@author: "comfact"
'''

import json
import requests

from .static import *

class Session:
    
    def __init__(self, ip, user, pwd, debug=False, week=False):
        try: requests.packages.urllib3.disable_warnings()
        except: pass
        self.debug = debug
        self.week = week
        self.session = requests.Session()
        self.url = 'https://%s' % ip
        login_url = self.url + '/api/aaaLogin.json'
        data = {'aaaUser': {'attributes': {'name': user, 'pwd': pwd}}}
        resp = self.session.post(login_url, data=json.dumps(data, sort_keys=True), verify=False)
        if not resp.status_code == 200: raise AcidipySessionError()
        
    def close(self):
        self.session.close()
        
    def get(self, url):
        if self.debug:
            print 'GET :', url
            resp = self.session.get(self.url + url)
            print 'CODE :', resp.status_code, '\n', resp.text
        else:
            resp = self.session.get(self.url + url)
        if resp.status_code == 200: return resp.json()['imdata']
        else:
            if not self.week:
                try:
                    error = resp.json()['imdata'][0]['error']['attributes']
                    code = error['code']
                    text = error['text']
                except: raise AcidipyError('?', 'Unknown')
                raise AcidipyError(code, text)
        return []
    
    def post(self, url, data):
        if self.debug:
            print 'POST :', url
            print data
            resp = self.session.post(self.url + url, data=data)
            print 'CODE :', resp.status_code, '\n', resp.text
        else:
            resp = self.session.post(self.url + url, data=data)
        if resp.status_code == 200: return True
        else:
            if not self.week:
                try:
                    error = resp.json()['imdata'][0]['error']['attributes']
                    code = error['code']
                    text = error['text']
                except: raise AcidipyError('?', 'Unknown')
                raise AcidipyError(code, text)
        return False
    
    def put(self, url, data):
        if self.debug:
            print 'PUT :', url
            print data
            resp = self.session.put(self.url + url, data=data)
            print 'CODE :', resp.status_code, '\n', resp.text
        else:
            resp = self.session.put(self.url + url, data=data)
        if resp.status_code == 200: return True
        else:
            if not self.week:
                try:
                    error = resp.json()['imdata'][0]['error']['attributes']
                    code = error['code']
                    text = error['text']
                except: raise AcidipyError('?', 'Unknown')
                raise AcidipyError(code, text)
        return False
    
    def delete(self, url):
        if self.debug:
            print 'DELETE :', url
            resp = self.session.delete(self.url + url)
            print 'CODE :', resp.status_code, '\n', resp.text
        else:
            resp = self.session.delete(self.url + url)
        if resp.status_code == 200: return True
        else:
            if not self.week:
                try:
                    error = resp.json()['imdata'][0]['error']['attributes']
                    code = error['code']
                    text = error['text']
                except: raise AcidipyError('?', 'Unknown')
                raise AcidipyError(code, text)
        return False
