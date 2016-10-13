'''
Created on 2016. 10. 13.

@author: "comfact"
'''

from .session import Domain
from .uni import Tenant, AppProf, BridgeDomain, EndPointGroup, Subnet

def deploy_aci(desc, verbose=False):
    
    try: dom_ip = desc['domain']['ip']
    except: exit(1)
    try: dom_user = desc['domain']['user']
    except: exit(1)
    try: dom_pwd = desc['domain']['pwd']
    except: exit(1)
    
    dom = Domain(dom_ip, dom_user, dom_pwd, False)
    if dom.is_active:
        if verbose: print 'Get Domain :', dom_ip, dom_user, dom_pwd
    else:
        if verbose: print 'Connection Failed :', dom_ip, dom_user, dom_pwd
        return
    
    tenant_objs = {}
    ap_objs = {}
    bd_objs = {}
    epg_objs = {}
    sn_objs = {}
    
    delete_tenants = []
    
    tenant_list = desc['tenant'] if 'tenant' in desc and isinstance(desc['tenant'], list) else [] 
    for tenant in tenant_list:
        tenant_obj = Tenant(tenant['name'])
        dom << tenant_obj
        tenant_objs[tenant_obj['dn']] = tenant_obj
        tenant_bd_objs = {}
        tenant_ap_objs = {}
        if verbose: print 'UPDATE >> fvTenant.dn=%s' % tenant_obj['dn']
        
        bd_list = tenant['bridge-domain'] if 'bridge-domain' in tenant and isinstance(tenant['bridge-domain'], list) else []
        for bd in bd_list:
            bd_obj = BridgeDomain(bd['name'])
            tenant_obj << bd_obj
            bd_objs[bd_obj['dn']] = bd_obj
            tenant_bd_objs[bd_obj['name']] = bd_obj
            if verbose: print 'UPDATE >> fvBD.dn=%s' % bd_obj['dn']
            
            sn_list = bd['subnet'] if 'subnet' in bd and isinstance(bd['subnet'], list) else []
            for sn in sn_list:
                sn_obj = Subnet(sn['ip'], name=sn['name'])
                bd_obj << sn_obj
                sn_objs[sn_obj['dn']] = sn_obj
                if verbose: print 'UPDATE >> fvSubnet.dn=%s' % sn_obj['dn']
        
        ap_list = tenant['app-prof'] if 'app-prof' in tenant and isinstance(tenant['app-prof'], list) else []
        for ap in ap_list:
            ap_obj = AppProf(ap['name'])
            tenant_obj << ap_obj
            ap_objs[ap_obj['dn']] = ap_obj
            tenant_ap_objs[ap_obj['name']] = ap_obj
            if verbose: print 'UPDATE >> fvAp.dn=%s' % ap_obj['dn']
            
            epg_list = ap['epg'] if 'epg' in ap and isinstance(ap['epg'], list) else []
            for epg in epg_list:
                epg_obj = EndPointGroup(epg['name'])
                ap_obj << epg_obj
                epg_objs[epg_obj['dn']] = epg_obj
                if verbose: print 'UPDATE >> fvAEPg.dn=%s' % epg_obj['dn']
                if 'rsbd' in epg:
                    tenant_bd_objs[epg['rsbd']] & epg_obj
                    if verbose: print 'RELATE >> fvAEPg.name=%s to fvBD.name=%s' % (epg_obj['name'], epg['rsbd'])
        
        if len(tenant_bd_objs) == 0 and len(tenant_ap_objs) == 0:
            delete_tenants.append(tenant['name'])
    
    def object_delete(obj):
        if verbose:
            print 'DELETE >> %s.dn=%s' % (obj._object, obj['dn'])
        obj.delete()
    
    def recursive_delete(obj):
        children = obj.getChildren()
        for child in children:
            if isinstance(child, BridgeDomain): recursive_delete(child)
            if isinstance(child, Subnet): recursive_delete(child)
            if isinstance(child, AppProf): recursive_delete(child)
            if isinstance(child, EndPointGroup): recursive_delete(child)
        
        if isinstance(obj, BridgeDomain):
            if obj['dn'] not in bd_objs: object_delete(obj)
        if isinstance(obj, Subnet):
            if obj['dn'] not in sn_objs: object_delete(obj)
        if isinstance(obj, AppProf):
            if obj['dn'] not in ap_objs: object_delete(obj)
        if isinstance(obj, EndPointGroup):
            if obj['dn'] not in epg_objs: object_delete(obj)
        
    for tenant in tenant_list:
        try: tenant_obj = Tenant.getList(dom, name=tenant['name'])[0]
        except: continue
        recursive_delete(tenant_obj)
        if tenant['name'] in delete_tenants:
            object_delete(tenant_obj)
    
    dom.close()
    