'''
Created on 2016. 10. 6.

@author: "comfact"
'''

import json
import time
import requests

from .static import *

class Session:
    
    def __init__(self, ip, user, pwd, conns=1, conn_max=2, debug=False, week=False):
        try: requests.packages.urllib3.disable_warnings()
        except: pass
        
        self.debug = debug
        self.week = week
        self.url = 'https://%s' % ip
        self.session = requests.Session()
        self.session.mount('https://', requests.adapters.HTTPAdapter(pool_connections=conns, pool_maxsize=conn_max))
        resp = self.session.post(self.url + '/api/aaaLogin.json', data=json.dumps({'aaaUser': {'attributes': {'name': user, 'pwd': pwd}}}, sort_keys=True), verify=False)
        if not resp.status_code == 200: raise AcidipySessionError()
        self.token = resp.cookies['APIC-cookie']
        self.cookie = 'APIC-cookie=' + self.token
    
    def close(self):
        self.session.close()
    
    def refresh(self):
        resp = self.session.get(self.url + '/api/aaaRefresh.json', cookies={'Set-Cookie' : self.cookie})
        if not resp.status_code == 200: raise AcidipySessionError()
        self.token = resp.cookies['APIC-cookie']
        self.cookie = 'APIC-cookie=' + self.token
            
    def get(self, url):
        if self.debug:
            print('GET : {}'.format(url))
            resp = self.session.get(self.url + url, verify=False, cookies={'Set-Cookie' : self.cookie})
            print('CODE : {}\n{}'.format(resp.status_code, resp.text))
        else:
            for i in range(0, 4):
                try: resp = self.session.get(self.url + url, verify=False, cookies={'Set-Cookie' : self.cookie})
                except Exception as e: time.sleep(0.5); continue
                else:
                    if resp.status_code == 200: return resp.json()['imdata']
                    else:
                        if not self.week:
                            try:
                                print resp.status_code
                                error = resp.json()['imdata'][0]['error']['attributes']
                                code = error['code']
                                text = error['text']
                            except: raise AcidipyError('?', 'Unknown')
                            raise AcidipyError(code, text)
        raise AcidipySessionError()
    
    def post(self, url, data):
        if self.debug:
            print('POST : {}'.format(url))
            print(data)
            resp = self.session.post(self.url + url, data=data, verify=False, cookies={'Set-Cookie' : self.cookie})
            print('CODE : {}\n{}'.format(resp.status_code, resp.text))
        else:
            for i in range(0, 4):
                try: resp = self.session.post(self.url + url, data=data, verify=False, cookies={'Set-Cookie' : self.cookie})
                except Exception as e: time.sleep(0.5); continue
                else:
                    if resp.status_code == 200: return True
                    else:
                        if not self.week:
                            try:
                                error = resp.json()['imdata'][0]['error']['attributes']
                                code = error['code']
                                text = error['text']
                            except: raise AcidipyError('?', 'Unknown')
                            raise AcidipyError(code, text)
        raise AcidipySessionError()
    
    def put(self, url, data):
        if self.debug:
            print('PUT : {}'.format(url))
            print(data)
            resp = self.session.put(self.url + url, data=data, verify=False, cookies={'Set-Cookie' : self.cookie})
            print('CODE : {}\n{}'.format(resp.status_code, resp.text))
        else:
            for i in range(0, 4):
                try: resp = self.session.put(self.url + url, data=data, verify=False, cookies={'Set-Cookie' : self.cookie})
                except Exception as e: time.sleep(0.5); continue
                else:
                    if resp.status_code == 200: return True
                    else:
                        if not self.week:
                            try:
                                error = resp.json()['imdata'][0]['error']['attributes']
                                code = error['code']
                                text = error['text']
                            except: raise AcidipyError('?', 'Unknown')
                            raise AcidipyError(code, text)
        raise AcidipySessionError()
    
    def delete(self, url):
        if self.debug:
            print('DELETE : {}'.format(url))
            resp = self.session.delete(self.url + url, verify=False, cookies={'Set-Cookie' : self.cookie})
            print('CODE : {}\n{}'.format(resp.status_code, resp.text))
        else:
            for i in range(0, 4):
                try: resp = self.session.delete(self.url + url, verify=False, cookies={'Set-Cookie' : self.cookie})
                except Exception as e: time.sleep(0.5); continue
                else:
                    if resp.status_code == 200: return True
                    else:
                        if not self.week:
                            try:
                                error = resp.json()['imdata'][0]['error']['attributes']
                                code = error['code']
                                text = error['text']
                            except: raise AcidipyError('?', 'Unknown')
                            raise AcidipyError(code, text)
        raise AcidipySessionError()
