'''
Created on 2016. 10. 26.

@author: "comfact"
'''

import re
from .model import Domain, TenantObject, ContractObject, VRFObject, BrDomObject, AppProfObject, SubnetObject, EPGObject

def deploy_aci(desc, verbose=False, debug=False):
    
    try: dom_ip = desc['Domain']['ip']
    except: exit(1)
    try: dom_user = desc['Domain']['user']
    except: exit(1)
    try: dom_pwd = desc['Domain']['pwd']
    except: exit(1)
    
    try: delete_empty_tenant = desc['Option']['deleteEmptyTenant']
    except: delete_empty_tenant = False
    
    try:
        dom = Domain(dom_ip, dom_user, dom_pwd, debug)
    except:
        if verbose: print 'Connection Failed :', dom_ip, dom_user, dom_pwd, '\n'
        exit(1)
    if verbose: print 'Get Domain :', dom_ip, dom_user, dom_pwd, '\n'
    
    tenant_objs = {}
    ctr_objs = {}
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
        tenant_obj = dom.Tenant.create(**parse_desc_unit(tenant))
        tenant_objs[tenant_obj['dn']] = tenant_obj
        if verbose: print 'UPDATE >> fvTenant.dn=%s\n' % tenant_obj['dn']
        
        tenant_ctr_objs = {}
        tenant_ctx_objs = {}
        tenant_bd_objs = {}
        tenant_sn_objs = {}
        tenant_ap_objs = {}
        tenant_epg_objs = {}
        
        #=======================================================================
        # Create & Update
        #=======================================================================
        ctr_list = tenant['Contract'] if 'Contract' in tenant and isinstance(tenant['Contract'], list) else []
        for ctr in ctr_list:
            ctr_obj = tenant_obj.Contract.create(**parse_desc_unit(ctr))
            if verbose: print 'UPDATE >> Contract:vzBrCP.dn=%s\n' % ctr_obj['dn']
            ctr_objs[ctr_obj['dn']] = ctr_obj
            tenant_ctr_objs[ctr_obj['name']] = ctr_obj
        
        ctx_list = tenant['VRF'] if 'VRF' in tenant and isinstance(tenant['VRF'], list) else []
        for ctx in ctx_list:
            ctx_obj = tenant_obj.VRF.create(**parse_desc_unit(ctx))
            if verbose: print 'UPDATE >> VRF:fvCtx.dn=%s\n' % ctx_obj['dn']
            ctx_objs[ctx_obj['dn']] = ctx_obj
            tenant_ctx_objs[ctx_obj['name']] = ctx_obj
        
        bd_list = tenant['BrDom'] if 'BrDom' in tenant and isinstance(tenant['BrDom'], list) else []
        for bd in bd_list:
            bd_obj = tenant_obj.BrDom.create(**parse_desc_unit(bd))
            if verbose: print 'UPDATE >> BrDom:fvBD.dn=%s\n' % bd_obj['dn']
            bd_objs[bd_obj['dn']] = bd_obj
            tenant_bd_objs[bd_obj['name']] = bd_obj
            
            sn_list = bd['Subnet'] if 'Subnet' in bd and isinstance(bd['Subnet'], list) else []
            for sn in sn_list:
                sn_obj = bd_obj.Subnet.create(**parse_desc_unit(sn))
                if verbose: print 'UPDATE >> Subnet:fvSubnet.dn=%s\n' % sn_obj['dn']
                sn_objs[sn_obj['dn']] = sn_obj
                tenant_sn_objs[sn_obj['name']] = sn_obj
        
        ap_list = tenant['AppProf'] if 'AppProf' in tenant and isinstance(tenant['AppProf'], list) else []
        for ap in ap_list:
            ap_obj = tenant_obj.AppProf.create(**parse_desc_unit(ap))
            if verbose: print 'UPDATE >> AppProf:fvAp.dn=%s\n' % ap_obj['dn']
            ap_objs[ap_obj['dn']] = ap_obj
            tenant_ap_objs[ap_obj['name']] = ap_obj
            
            epg_list = ap['EPG'] if 'EPG' in ap and isinstance(ap['EPG'], list) else []
            for epg in epg_list:
                epg_obj = ap_obj.EPG.create(**parse_desc_unit(epg))
                if verbose: print 'UPDATE >> EPG:fvAEPg.dn=%s\n' % epg_obj['dn']
                epg_objs[epg_obj['dn']] = epg_obj
                tenant_epg_objs[epg_obj['name']] = epg_obj
        
        #=======================================================================
        # Relations
        #=======================================================================
        for bd in bd_list:
            if 'VRF@' in bd:
                tenant_bd_objs[bd['name']].relate2VRF(tenant_ctx_objs[bd['VRF@']])
                if verbose: print 'RELATE >> BrDom:fvBD.name=%s to VRF:fvCtx.name=%s\n' % (bd['name'], bd['VRF@'])
                
        for ap in ap_list:
            epg_list = ap['EPG'] if 'EPG' in ap and isinstance(ap['EPG'], list) else []
            for epg in epg_list:
                if 'BrDom@' in epg:
                    tenant_epg_objs[epg['name']].relate2BrDom(tenant_bd_objs[epg['BrDom@']])
                    if verbose: print 'RELATE >> EPG:fvAEPg.name=%s to BrDom:fvBD.name=%s\n' % (epg_obj['name'], epg['BrDom@'])
                if 'Cons@' in epg:
                    for cons in epg['Cons@']:
                        tenant_epg_objs[epg['name']].relate2Consumer(tenant_ctr_objs[cons])
                        if verbose: print 'RELATE >> EPG:fvAEPg.name=%s to Consume:vzBrCP.name=%s\n' % (epg_obj['name'], cons)
                if 'Prov@' in epg:
                    for prov in epg['Prov@']:
                        tenant_epg_objs[epg['name']].relate2Provider(tenant_ctr_objs[prov])
                        if verbose: print 'RELATE >> EPG:fvAEPg.name=%s to Provide:vzBrCP.name=%s\n' % (epg_obj['name'], prov)
                if 'Path@' in epg:
                    for path in epg['Path@']:
                        ep_obj = dom.Pod(path['Pod@']).Paths(path['Node@']).Path(path['Intf@'])
                        tenant_epg_objs[epg['name']].relate2StaticPath(ep_obj, **parse_desc_unit(path))
                        if verbose: print 'RELATE >> EPG:fvAEPg.name=%s to Path:PathEp.name=%s\n' % (epg_obj['name'], path['Pod@'] + '/' + path['Node@'] + '/' + path['Intf@'])
        
        if delete_empty_tenant and len(tenant_ctx_objs) == 0 and len(tenant_bd_objs) == 0 and len(tenant_ap_objs) == 0:
            delete_tenants.append(tenant['name'])
    
    def object_delete(obj):
        dn = obj['dn']
        obj.delete()
        if verbose: print 'DELETE >> %s.dn=%s\n' % (obj.class_name, dn)
    
    def recursive_delete(obj):
        children = obj.children()
        for child in children:
            if isinstance(child, ContractObject): recursive_delete(child)
            elif isinstance(child, VRFObject): recursive_delete(child)
            elif isinstance(child, BrDomObject): recursive_delete(child)
            elif isinstance(child, SubnetObject): recursive_delete(child)
            elif isinstance(child, AppProfObject): recursive_delete(child)
            elif isinstance(child, EPGObject): recursive_delete(child)
        
        if isinstance(obj, ContractObject):
            if obj['dn'] not in ctr_objs: object_delete(obj)
        elif isinstance(obj, VRFObject):
            if obj['dn'] not in ctx_objs: object_delete(obj)
        elif isinstance(obj, BrDomObject):
            if obj['dn'] not in bd_objs: object_delete(obj)
        elif isinstance(obj, AppProfObject):
            if obj['dn'] not in ap_objs: object_delete(obj)
        elif isinstance(obj, SubnetObject):
            if obj['dn'] not in sn_objs: object_delete(obj)
        elif isinstance(obj, EPGObject):
            if obj['dn'] not in epg_objs: object_delete(obj)
        
    for tenant in tenant_list:
        try: tenant_obj = dom.Tenant(tenant['name'])
        except: continue
        recursive_delete(tenant_obj)
        if tenant['name'] in delete_tenants:
            object_delete(tenant_obj)
    
    dom.close()