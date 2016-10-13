'''
Created on 2016. 10. 11.

@author: "comfact"
'''

class Health(dict):
    
    def __init__(self, dn, score):
        dict.__init__(self, dn=dn, score=score)