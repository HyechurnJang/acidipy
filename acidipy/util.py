'''
Created on 2016. 10. 13.

@author: "comfact"
'''

import re
from .session import Domain
from .uni import Tenant, AppProf, BridgeDomain, Context, EndPointGroup, Subnet

def deploy_aci(desc, verbose=False, debug=False):
    
    try: dom_ip = desc['Domain']['ip']
    except: exit(1)
    try: dom_user = desc['Domain']['user']
    except: exit(1)
    try: dom_pwd = desc['Domain']['pwd']
    except: exit(1)
    
    try: delete_empty_tenant = desc['Option']['deleteEmptyTenant']
    except: delete_empty_tenant = False
    
    dom = Domain(dom_ip, dom_user, dom_pwd, debug)
    if dom.is_active:
        if verbose: print 'Get Domain :', dom_ip, dom_user, dom_pwd, '\n'
    else:
        if verbose: print 'Connection Failed :', dom_ip, dom_user, dom_pwd, '\n'
        return
    
    tenant_objs = {}
    ctx_objs = {}
    bd_objs = {}
    sn_objs = {}
    ap_objs = {}
    epg_objs = {}
    
    delete_tenants = []
    
    def parse_desc_unit(unit):
        ret = {}
        for key in unit:
            if re.search('^[a-z]\w*', key): ret[key] = unit[key]
        return ret
    
    tenant_list = desc['Tenant'] if 'Tenant' in desc and isinstance(desc['Tenant'], list) else []
    for tenant in tenant_list:
        tenant_obj = Tenant(**parse_desc_unit(tenant))
        dom << tenant_obj
        tenant_objs[tenant_obj['dn']] = tenant_obj
        if verbose: print 'UPDATE >> fvTenant.dn=%s\n' % tenant_obj['dn']
        
        tenant_ctx_objs = {}
        tenant_bd_objs = {}
        tenant_sn_objs = {}
        tenant_ap_objs = {}
        tenant_epg_objs = {}
        
        #=======================================================================
        # Create & Update
        #=======================================================================
        ctx_list = tenant['Context'] if 'Context' in tenant and isinstance(tenant['Context'], list) else []
        for ctx in ctx_list:
            ctx_obj = Context(**parse_desc_unit(ctx))
            tenant_obj << ctx_obj
            if verbose: print 'UPDATE >> fvCtx.dn=%s\n' % ctx_obj['dn']
            ctx_objs[ctx_obj['dn']] = ctx_obj
            tenant_ctx_objs[ctx_obj['name']] = ctx_obj
        
        bd_list = tenant['BridgeDomain'] if 'BridgeDomain' in tenant and isinstance(tenant['BridgeDomain'], list) else []
        for bd in bd_list:
            bd_obj = BridgeDomain(**parse_desc_unit(bd))
            tenant_obj << bd_obj
            if verbose: print 'UPDATE >> fvBD.dn=%s\n' % bd_obj['dn']
            bd_objs[bd_obj['dn']] = bd_obj
            tenant_bd_objs[bd_obj['name']] = bd_obj
            
            sn_list = bd['Subnet'] if 'Subnet' in bd and isinstance(bd['Subnet'], list) else []
            for sn in sn_list:
                sn_obj = Subnet(**parse_desc_unit(sn))
                bd_obj << sn_obj
                if verbose: print 'UPDATE >> fvSubnet.dn=%s\n' % sn_obj['dn']
                sn_objs[sn_obj['dn']] = sn_obj
                tenant_sn_objs[sn_obj['name']] = sn_obj
        
        ap_list = tenant['AppProf'] if 'AppProf' in tenant and isinstance(tenant['AppProf'], list) else []
        for ap in ap_list:
            ap_obj = AppProf(**parse_desc_unit(ap))
            tenant_obj << ap_obj
            if verbose: print 'UPDATE >> fvAp.dn=%s\n' % ap_obj['dn']
            ap_objs[ap_obj['dn']] = ap_obj
            tenant_ap_objs[ap_obj['name']] = ap_obj
            
            epg_list = ap['EndPointGroup'] if 'EndPointGroup' in ap and isinstance(ap['EndPointGroup'], list) else []
            for epg in epg_list:
                epg_obj = EndPointGroup(**parse_desc_unit(epg))
                ap_obj << epg_obj
                if verbose: print 'UPDATE >> fvAEPg.dn=%s\n' % epg_obj['dn']
                epg_objs[epg_obj['dn']] = epg_obj
                tenant_epg_objs[epg_obj['name']] = epg_obj
        
        #=======================================================================
        # Relations
        #=======================================================================
        for bd in bd_list:
            if 'Context@' in bd:
                tenant_ctx_objs[bd['Context@']] & tenant_bd_objs[bd['name']]
                if verbose: print 'RELATE >> fvBD.name=%s to fvCtx.name=%s\n' % (bd['name'], bd['Context@'])
                
        for ap in ap_list:
            epg_list = ap['EndPointGroup'] if 'EndPointGroup' in ap and isinstance(ap['EndPointGroup'], list) else []
            for epg in epg_list:
                if 'BridgeDomain@' in epg:
                    tenant_bd_objs[epg['BridgeDomain@']] & tenant_epg_objs[epg['name']]
                    if verbose: print 'RELATE >> fvAEPg.name=%s to fvBD.name=%s\n' % (epg_obj['name'], epg['BridgeDomain@'])
        
        if delete_empty_tenant and len(tenant_ctx_objs) == 0 and len(tenant_bd_objs) == 0 and len(tenant_ap_objs) == 0:
            delete_tenants.append(tenant['name'])
    
    def object_delete(obj):
        dn = obj['dn']
        obj.delete()
        if verbose: print 'DELETE >> %s.dn=%s\n' % (obj._object, dn)
    
    def recursive_delete(obj):
        children = obj.getChildren()
        for child in children:
            if isinstance(child, BridgeDomain): recursive_delete(child)
            if isinstance(child, Subnet): recursive_delete(child)
            if isinstance(child, AppProf): recursive_delete(child)
            if isinstance(child, EndPointGroup): recursive_delete(child)
            if isinstance(child, Context): recursive_delete(child)
        
        if isinstance(obj, BridgeDomain):
            if obj['dn'] not in bd_objs: object_delete(obj)
        if isinstance(obj, Subnet):
            if obj['dn'] not in sn_objs: object_delete(obj)
        if isinstance(obj, AppProf):
            if obj['dn'] not in ap_objs: object_delete(obj)
        if isinstance(obj, EndPointGroup):
            if obj['dn'] not in epg_objs: object_delete(obj)
        if isinstance(obj, Context):
            if obj['dn'] not in ctx_objs: object_delete(obj)
        
    for tenant in tenant_list:
        try: tenant_obj = Tenant.getList(dom, name=tenant['name'])[0]
        except: continue
        recursive_delete(tenant_obj)
        if tenant['name'] in delete_tenants:
            object_delete(tenant_obj)
    
    dom.close()
    