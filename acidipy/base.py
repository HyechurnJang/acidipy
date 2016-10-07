'''
Created on 2016. 10. 6.

@author: "comfact"
'''

import json

class ACIObject(dict):
    _PARENT = None
    _CHILD = []
    
    def __init__(self, _object=None, _domain=None, _detail=False, **attributes):
        dict.__init__(self, **attributes)
        if _object == None: self._object = self.__class__._OBJECT
        else: self._object = _object
        self._domain = _domain
        self._detail = _detail
        
    def __str__(self):
        return dict.__str__(self)
    
    def __lshift__(self, obj):
        if obj._OBJECT in self._CHILD: return obj.create(self)
        if obj._OBJECT in self._RSOBJ: return self.relate(obj)
        if obj._OBJECT in self._RTOBJ: return obj.relate(self)
        return False
    
    def toJson(self):
        data = {}
        data[self._object] = {'attributes' : self}
        return json.dumps(data, sort_keys=True)
    
    def relate(self, rel):
        return False
    
    #===========================================================================
    # Level 3 API
    #===========================================================================
    @classmethod
    def getList(cls, domain, detail=False, **clause):
        return domain.getList(cls._OBJECT, detail, **clause)
    
    def getRefresh(self):
        if not self._detail: return self
        data = self._domain.get('/api/mo/' + self['dn'] + '.json')
        for d in data:
            attrs = d[self._object]['attributes']
            for attr_key in attrs: self[attr_key] = attrs[attr_key]
            self._detail = True
            break
        return self
    
    def getDetail(self):
        if self._detail: return self
        data = self._domain.get('/api/mo/' + self['dn'] + '.json')
        for d in data:
            attrs = d[self._object]['attributes']
            for attr_key in attrs: self[attr_key] = attrs[attr_key]
            self._detail = True
            break
        return self
    
    def getParent(self, detail=False):
        if self._PARENT == None: return None
        try: dn = self['dn'].split(self._IDENTY)[0]
        except: return None
        try: return self._domain.getOne(dn, detail)
        except: return None
        
    def getChildren(self, detail=False):
        return self._domain.getChildren(self['dn'], detail)
    
    def create(self, parent):
        if self._PARENT != parent._OBJECT: return False
        if parent._OBJECT == 'Domain':
            ret = parent.create('uni', self.toJson())
            if ret:
                self['dn'] = 'uni' + self._IDENTY + self._PKTMPL % self[self._PRIKEY]
                self._domain = parent
        else:
            ret = parent._domain.create(parent['dn'], self.toJson())
            if ret:
                self['dn'] = parent['dn'] + self._IDENTY + self._PKTMPL % self[self._PRIKEY]
                self._domain = parent._domain
        return ret
    
    def update(self):
        ret = self._domain.update(self['dn'], self.toJson())
        if ret: self.getRefresh()
        return ret
    
    def delete(self):
        ret = self._domain.delete(self['dn'])
        if ret:
            self._domain = None
            self.pop('dn')
        return ret
