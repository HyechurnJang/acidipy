'''
Created on 2016. 10. 6.

@author: "comfact"
'''

import json
import time
import requests

from .static import *

class Session:
    
    def __init__(self, ip, user, pwd, conns=1, conn_max=2, retry=3, debug=False, week=False):
        try: requests.packages.urllib3.disable_warnings()
        except: pass
        
        self.ip = ip
        self.user = user
        self.pwd = pwd
        self.conns = conns
        self.conn_max = conn_max
        self.retry = retry
        self.debug = debug
        self.week = week
        self.url = 'https://%s' % ip
        self.session = None
        self.token = None
        self.cookie = None
        
        self.login()
    
    def login(self):
        if self.session != None: self.session.close()
        try:
            self.session = requests.Session()
            self.session.mount('https://', requests.adapters.HTTPAdapter(pool_connections=self.conns, pool_maxsize=self.conn_max))
            for i in range(0, self.retry):
                resp = self.session.post(self.url + '/api/aaaLogin.json', data=json.dumps({'aaaUser': {'attributes': {'name': self.user, 'pwd': self.pwd}}}), verify=False)
                if resp.status_code == 200:
                    self.token = resp.cookies['APIC-cookie']
                    self.cookie = 'APIC-cookie=' + self.token
                    if self.debug: print('Session %s with %s' % (self.url, self.token))
                    return
            raise AcidipySessionError()
        except: raise AcidipySessionError()
    
    def refresh(self):
        try:
            for i in range(0, self.retry):
                resp = self.session.get(self.url + '/api/aaaRefresh.json', cookies={'Set-Cookie' : self.cookie})
                if resp.status_code == 200:
                    self.token = resp.cookies['APIC-cookie']
                    self.cookie = 'APIC-cookie=' + self.token
                    if self.debug: print('Refresh %s with %s' % (self.url, self.token))
                    return
            self.login()
        except: raise AcidipySessionError()
    
    def close(self):
        if self.session != None:
            self.session.close()
            self.session = None
            
    def get(self, url):
        if self.debug:
            print('GET : {}'.format(url))
            resp = self.session.get(self.url + url, verify=False, cookies={'Set-Cookie' : self.cookie})
            print('CODE : {}\n{}'.format(resp.status_code, resp.text))
            return resp.json()['imdata']
        for i in range(0, self.retry):
            try: resp = self.session.get(self.url + url, verify=False, cookies={'Set-Cookie' : self.cookie})
            except: time.sleep(0.5); continue
            if resp.status_code == 200: return resp.json()['imdata']
            elif resp.status_code == 403: self.refresh()
            else:
                if not self.week:
                    try:
                        error = resp.json()['imdata'][0]['error']['attributes']
                        code = error['code']
                        text = error['text']
                    except: raise AcidipyError('?', 'Unknown')
                    else: raise AcidipyError(code, text)
        raise AcidipySessionError()
    
    def post(self, url, data):
        if self.debug:
            print('POST : {}'.format(url)); print(data)
            resp = self.session.post(self.url + url, data=data, verify=False, cookies={'Set-Cookie' : self.cookie})
            print('CODE : {}\n{}'.format(resp.status_code, resp.text))
            return True
        for i in range(0, self.retry):
            try: resp = self.session.post(self.url + url, data=data, verify=False, cookies={'Set-Cookie' : self.cookie})
            except: time.sleep(0.5); continue
            if resp.status_code == 200: return True
            elif resp.status_code == 403: self.refresh()
            else:
                if not self.week:
                    try:
                        error = resp.json()['imdata'][0]['error']['attributes']
                        code = error['code']
                        text = error['text']
                    except: raise AcidipyError('?', 'Unknown')
                    else: raise AcidipyError(code, text)
        raise AcidipySessionError()
    
    def put(self, url, data):
        if self.debug:
            print('PUT : {}'.format(url)); print(data)
            resp = self.session.put(self.url + url, data=data, verify=False, cookies={'Set-Cookie' : self.cookie})
            print('CODE : {}\n{}'.format(resp.status_code, resp.text))
            return True
        for i in range(0, self.retry):
            try: resp = self.session.put(self.url + url, data=data, verify=False, cookies={'Set-Cookie' : self.cookie})
            except: time.sleep(0.5); continue
            if resp.status_code == 200: return True
            elif resp.status_code == 403: self.refresh()
            else:
                if not self.week:
                    try:
                        error = resp.json()['imdata'][0]['error']['attributes']
                        code = error['code']
                        text = error['text']
                    except: raise AcidipyError('?', 'Unknown')
                    else: raise AcidipyError(code, text)
        raise AcidipySessionError()
    
    def delete(self, url):
        if self.debug:
            print('DELETE : {}'.format(url))
            resp = self.session.delete(self.url + url, verify=False, cookies={'Set-Cookie' : self.cookie})
            print('CODE : {}\n{}'.format(resp.status_code, resp.text))
            return True
        for i in range(0, self.retry):
            try: resp = self.session.delete(self.url + url, verify=False, cookies={'Set-Cookie' : self.cookie})
            except: time.sleep(0.5); continue
            if resp.status_code == 200: return True
            elif resp.status_code == 403: self.refresh()
            else:
                if not self.week:
                    try:
                        error = resp.json()['imdata'][0]['error']['attributes']
                        code = error['code']
                        text = error['text']
                    except: raise AcidipyError('?', 'Unknown')
                    else: raise AcidipyError(code, text)
        raise AcidipySessionError()
