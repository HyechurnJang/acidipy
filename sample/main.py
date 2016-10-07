'''
Created on 2016. 10. 6.

@author: "comfact"
'''

from acidipy import *

if __name__ == '__main__':
    
    dom = Domain('APIC DOMAIN', 'USER', 'PASSWORD')
    
    print '\nRESULT1 #####################################################\n'
    print '1. Tenants'
    tenants = Tenant.getList(dom)
    for t in tenants: print t
    print '2. Bridge Domain'
    bds = BridgeDomain.getList(dom)
    for b in bds: print b
    print '3. Subnet'
    sns = Subnet.getList(dom)
    for s in sns: print s
    print '4. App Profile'
    aps = AppProf.getList(dom)
    for a in aps: print a
    print '5. End Point Group'
    epgs = EndPointGroup.getList(dom)
    for e in epgs: print e
    
    print '\nCREATE #####################################################\n'
    
#     print '## METHOD 1'
#     hyjang = Tenant('hyjang')
#     print hyjang.create(dom)
#     print hyjang.getDetail()
#     print ''
#     hj_bd = BridgeDomain('testbd')
#     print hj_bd.create(hyjang)
#     print hj_bd.getDetail()
#     print ''
#     hj_sn = Subnet('testsub', '192.168.1.1/24')
#     print hj_sn.create(hj_bd)
#     print hj_sn.getDetail()
#     print ''
#     hj_ap = AppProf('testap')
#     print hj_ap.create(hyjang)
#     print hj_ap.getDetail()
#     print ''
#     hj_epg = EndPointGroup('testepg')
#     print hj_epg.create(hj_ap)
#     print hj_epg.getDetail()
#     print hj_epg.relate(hj_bd)
#     print ''
    
    print '## METHOD 2'
    hyjang = Tenant('hyjang')
    print dom << hyjang
    print hyjang.getDetail()
    print ''
    hj_bd = BridgeDomain('testbd')
    print hyjang << hj_bd
    print hj_bd.getDetail()
    print ''
    hj_sn = Subnet('testsub', '192.168.1.1/24')
    print hj_bd << hj_sn
    print hj_sn.getDetail()
    print ''
    hj_ap = AppProf('testap')
    print hyjang << hj_ap
    print hj_ap.getDetail()
    print ''
    hj_epg = EndPointGroup('testepg')
    print hj_ap << hj_epg
    print hj_epg.getDetail()
    print hj_bd & hj_epg
    print ''
     
    print '\nRESULT2 #####################################################\n'
    print '1. Tenants'
    tenants = Tenant.getList(dom, detail=True, name='hyjang')
    for t in tenants: print t
    print '2. Bridge Domain'
    bds = BridgeDomain.getList(dom, detail=True, name='testbd')
    for b in bds: print b
    print '3. Subnet'
    sns = Subnet.getList(dom, detail=True, name='testsub')
    for s in sns: print s
    print '4. App Profile'
    aps = AppProf.getList(dom, detail=True, name='testap')
    for a in aps: print a
    print '5. End Point Group'
    epgs = EndPointGroup.getList(dom, detail=True, name='testepg')
    for e in epgs: print e
          
    print ''
    raw_input('Press Any Key to Delete >')
        
    print '\nDELETE #####################################################\n'
    
    print hj_epg.delete()
    print hj_ap.delete()
    print hj_sn.delete()
    print hj_bd.delete()
    print hyjang.delete()
    print ''
         
    print '\nRESULT3 #####################################################\n'
    print '1. Tenants'
    tenants = Tenant.getList(dom, detail=True, name='hyjang')
    for t in tenants: print t
    print '2. Bridge Domain'
    bds = BridgeDomain.getList(dom, detail=True, name='testbd')
    for b in bds: print b
    print '3. Subnet'
    sns = Subnet.getList(dom, detail=True, name='testsub')
    for s in sns: print s
    print '4. App Profile'
    aps = AppProf.getList(dom, detail=True, name='testap')
    for a in aps: print a
    print '5. End Point Group'
    epgs = EndPointGroup.getList(dom, detail=True, name='testepg')
    for e in epgs: print e
     
    dom.close() 