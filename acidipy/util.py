'''
Created on 2016. 10. 26.

@author: "comfact"
'''

import re
from .model import Controller, TenantObject, FilterObject, ContractObject, ContextObject, L3OutObject, L3ProfileObject, BridgeDomainObject, AppProfileObject, FilterEntryObject, SubjectObject, SubnetObject, EPGObject

def deployACI(desc, verbose=False, debug=False):
    
    try: dom_ip = desc['Controller']['ip']
    except: exit(1)
    try: dom_user = desc['Controller']['user']
    except: exit(1)
    try: dom_pwd = desc['Controller']['pwd']
    except: exit(1)
    
    try: delete_empty_tenant = desc['Option']['deleteEmptyTenant']
    except: delete_empty_tenant = False
    try: deploy_incremental = desc['Option']['deployIncremental']
    except: deploy_incremental = False
    
    try:
        dom = Controller(dom_ip, dom_user, dom_pwd, debug=debug)
    except:
        if verbose: print('Connection Failed : %s, %s, %s\n' % (dom_ip, dom_user, dom_pwd))
        exit(1)
    if verbose: print('Get Controller : %s, %s, %s\n' % (dom_ip, dom_user, dom_pwd))
    
    common = dom.Tenant('common')
    
    tenant_objs = {}
    flt_objs = {}
    ctr_objs = {}
    ctx_objs = {}
    l3e_objs = {}
    bd_objs = {}
    fe_objs = {}
    sj_objs = {}
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
        if verbose: print('UPDATE >> fvTenant.dn=%s\n' % tenant_obj['dn'])
        
        tenant_flt_objs = {}
        tenant_ctr_objs = {}
        tenant_ctx_objs = {}
        tenant_l3e_objs = {}
        tenant_bd_objs = {}
        tenant_fe_objs = {}
        tenant_sj_objs = {}
        tenant_sn_objs = {}
        tenant_ap_objs = {}
        tenant_epg_objs = {}
        
        #=======================================================================
        # Create & Update
        #=======================================================================
        flt_list = tenant['Filter'] if 'Filter' in tenant and isinstance(tenant['Filter'], list) else []
        for flt in flt_list:
            flt_obj = tenant_obj.Filter.create(**parse_desc_unit(flt))
            if verbose: print('UPDATE >> Filter:vzFilter.dn=%s\n' % flt_obj['dn'])
            flt_objs[flt_obj['dn']] = flt_obj
            tenant_flt_objs[flt_obj['name']] = flt_obj
            
            fe_list = flt['FilterEntry'] if 'FilterEntry' in flt and isinstance(flt['FilterEntry'], list) else []
            for fe in fe_list:
                fe_obj = flt_obj.FilterEntry.create(**parse_desc_unit(fe))
                if verbose: print('UPDATE >> FilterEntry:vzEntry.dn=%s\n' % fe_obj['dn'])
                fe_objs[fe_obj['dn']] = fe_obj
                tenant_fe_objs[fe_obj['name']] = fe_obj
        
        ctr_list = tenant['Contract'] if 'Contract' in tenant and isinstance(tenant['Contract'], list) else []
        for ctr in ctr_list:
            ctr_obj = tenant_obj.Contract.create(**parse_desc_unit(ctr))
            if verbose: print('UPDATE >> Contract:vzBrCP.dn=%s\n' % ctr_obj['dn'])
            ctr_objs[ctr_obj['dn']] = ctr_obj
            tenant_ctr_objs[ctr_obj['name']] = ctr_obj
            
            sj_list = ctr['Subject'] if 'Subject' in ctr and isinstance(ctr['Subject'], list) else []
            for sj in sj_list:
                sj_obj = ctr_obj.Subject.create(**parse_desc_unit(sj))
                if verbose: print('UPDATE >> Subject:vzSubj.dn=%s\n' % sj_obj['dn'])
                sj_objs[sj_obj['dn']] = sj_obj
                tenant_sj_objs[sj_obj['name']] = sj_obj
        
        ctx_list = tenant['Context'] if 'Context' in tenant and isinstance(tenant['Context'], list) else []
        for ctx in ctx_list:
            ctx_obj = tenant_obj.Context.create(**parse_desc_unit(ctx))
            if verbose: print('UPDATE >> Context:fvCtx.dn=%s\n' % ctx_obj['dn'])
            ctx_objs[ctx_obj['dn']] = ctx_obj
            tenant_ctx_objs[ctx_obj['name']] = ctx_obj
            
        l3e_list = tenant['L3External'] if 'L3External' in tenant and isinstance(tenant['L3External'], list) else []
        for l3e in l3e_list:
            l3e_obj = tenant_obj.L3Out.create(**parse_desc_unit(l3e))
            if verbose: print('UPDATE >> L3External:l3extOut.dn=%s\n' % l3e_obj['dn'])
            l3e_objs[l3e_obj['dn']] = l3e_obj
            tenant_l3e_objs[l3e_obj['name']] = l3e_obj
        
        bd_list = tenant['BridgeDomain'] if 'BridgeDomain' in tenant and isinstance(tenant['BridgeDomain'], list) else []
        for bd in bd_list:
            bd_obj = tenant_obj.BridgeDomain.create(**parse_desc_unit(bd))
            if verbose: print('UPDATE >> BridgeDomain:fvBD.dn=%s\n' % bd_obj['dn'])
            bd_objs[bd_obj['dn']] = bd_obj
            tenant_bd_objs[bd_obj['name']] = bd_obj
            
            sn_list = bd['Subnet'] if 'Subnet' in bd and isinstance(bd['Subnet'], list) else []
            for sn in sn_list:
                sn_obj = bd_obj.Subnet.create(**parse_desc_unit(sn))
                if verbose: print('UPDATE >> Subnet:fvSubnet.dn=%s\n' % sn_obj['dn'])
                sn_objs[sn_obj['dn']] = sn_obj
                tenant_sn_objs[sn_obj['name']] = sn_obj
        
        ap_list = tenant['AppProfile'] if 'AppProfile' in tenant and isinstance(tenant['AppProfile'], list) else []
        for ap in ap_list:
            ap_obj = tenant_obj.AppProfile.create(**parse_desc_unit(ap))
            if verbose: print('UPDATE >> AppProfile:fvAp.dn=%s\n' % ap_obj['dn'])
            ap_objs[ap_obj['dn']] = ap_obj
            tenant_ap_objs[ap_obj['name']] = ap_obj
            
            epg_list = ap['EPG'] if 'EPG' in ap and isinstance(ap['EPG'], list) else []
            for epg in epg_list:
                epg_obj = ap_obj.EPG.create(**parse_desc_unit(epg))
                if verbose: print('UPDATE >> EPG:fvAEPg.dn=%s\n' % epg_obj['dn'])
                epg_objs[epg_obj['dn']] = epg_obj
                tenant_epg_objs[epg_obj['name']] = epg_obj
        
        #=======================================================================
        # Relations
        #=======================================================================
        for ctr in ctr_list:
            sj_list = ctr['Subject'] if 'Subject' in ctr and isinstance(ctr['Subject'], list) else []
            for sj in sj_list:
                if 'Filter' in sj:
                    for flt in sj['Filter']:
                        try: tenant_sj_objs[sj['name']].relate(tenant_flt_objs[flt])
                        except:
                            try: tenant_sj_objs[sj['name']].relate(common.Filter(flt))
                            except:
                                if verbose: print('RELATE FAILED >> Subject:vzSubj.name=%s to Filter:vzFilter.name=%s\n' % (sj['name'], flt))
                        if verbose: print('RELATE >> Subject:vzSubj.name=%s to Filter:vzFilter.name=%s\n' % (sj['name'], flt))
        
        for l3e in l3e_list:
            if 'Context' in l3e:
                try: tenant_l3e_objs[l3e['name']].relate(tenant_ctx_objs[l3e['Context']])
                except:
                    try: tenant_l3e_objs[l3e['name']].relate(common.Context(l3e['Context']))
                    except:
                        if verbose: print('RELATE FAILED>> L3External:l3extOut.name=%s to Context:fvCtx.name=%s\n' % (bd['name'], bd['Context']))
                if verbose: print('RELATE >> L3External:l3extOut.name=%s to Context:fvCtx.name=%s\n' % (bd['name'], bd['Context']))
        
        for bd in bd_list:
            if 'Context' in bd:
                try: tenant_bd_objs[bd['name']].relate(tenant_ctx_objs[bd['Context']])
                except:
                    try: tenant_bd_objs[bd['name']].relate(common.Context(bd['Context']))
                    except:
                        if verbose: print('RELATE FAILED>> BridgeDomain:fvBD.name=%s to Context:fvCtx.name=%s\n' % (bd['name'], bd['Context']))
                if verbose: print('RELATE >> BridgeDomain:fvBD.name=%s to Context:fvCtx.name=%s\n' % (bd['name'], bd['Context']))
            if 'L3External' in bd:
                try: tenant_bd_objs[bd['name']].relate(tenant_l3e_objs[bd['L3External']])
                except:
                    try: tenant_bd_objs[bd['name']].relate(common.L3External(bd['L3External']))
                    except:
                        if verbose: print('RELATE FAILED>> BridgeDomain:fvBD.name=%s to L3External:l3extOut.name=%s\n' % (bd['name'], bd['L3External']))
                if verbose: print('RELATE >> BridgeDomain:fvBD.name=%s to L3External:l3extOut.name=%s\n' % (bd['name'], bd['L3External']))
                
        for ap in ap_list:
            epg_list = ap['EPG'] if 'EPG' in ap and isinstance(ap['EPG'], list) else []
            for epg in epg_list:
                if 'BridgeDomain' in epg:
                    try: tenant_epg_objs[epg['name']].relate(tenant_bd_objs[epg['BridgeDomain']])
                    except:
                        try: tenant_epg_objs[epg['name']].relate(common.BridgeDomain(epg['BridgeDomain']))
                        except:
                            if verbose: print('RELATE FAILED>> EPG:fvAEPg.name=%s to BridgeDomain:fvBD.name=%s\n' % (epg_obj['name'], epg['BridgeDomain']))
                    if verbose: print('RELATE >> EPG:fvAEPg.name=%s to BridgeDomain:fvBD.name=%s\n' % (epg_obj['name'], epg['BridgeDomain']))
                if 'Consume' in epg:
                    for cons in epg['Consume']:
                        try: tenant_epg_objs[epg['name']].relate(tenant_ctr_objs[cons])
                        except:
                            try: tenant_epg_objs[epg['name']].relate(common.Contract(cons))
                            except:
                                if verbose: print('RELATE FAILED>> EPG:fvAEPg.name=%s to Consume:vzBrCP.name=%s\n' % (epg_obj['name'], cons))
                        if verbose: print('RELATE >> EPG:fvAEPg.name=%s to Consume:vzBrCP.name=%s\n' % (epg_obj['name'], cons))
                if 'Provide' in epg:
                    for prov in epg['Provide']:
                        try: tenant_epg_objs[epg['name']].relate(tenant_ctr_objs[prov])
                        except:
                            try: tenant_epg_objs[epg['name']].relate(common.Contract(prov))
                            except:
                                if verbose: print('RELATE FAILED>> EPG:fvAEPg.name=%s to Provide:vzBrCP.name=%s\n' % (epg_obj['name'], prov))
                        if verbose: print('RELATE >> EPG:fvAEPg.name=%s to Provide:vzBrCP.name=%s\n' % (epg_obj['name'], prov))
                if 'Path' in epg:
                    for path in epg['Path']:
                        ep_obj = dom.Pod(path['Pod']).Paths(path['Node']).Path(path['Intf'])
                        tenant_epg_objs[epg['name']].relate(ep_obj, **parse_desc_unit(path))
                        if verbose: print('RELATE >> EPG:fvAEPg.name=%s to Path:PathEp.name=%s\n' % (epg_obj['name'], path['Pod'] + '/' + path['Node'] + '/' + path['Intf']))
        
        if delete_empty_tenant and len(tenant_ctx_objs) == 0 and len(tenant_bd_objs) == 0 and len(tenant_ap_objs) == 0:
            delete_tenants.append(tenant['name'])
    
    def object_delete(obj):
        dn = obj['dn']
        obj.delete()
        if verbose: print('DELETE >> %s.dn=%s\n' % (obj.class_name, dn))
    
    def recursive_delete(obj):
        children = obj.children()
        for child in children:
            if isinstance(child, FilterObject): recursive_delete(child)
            elif isinstance(child, ContractObject): recursive_delete(child)
            elif isinstance(child, ContextObject): recursive_delete(child)
            elif isinstance(child, L3OutObject): recursive_delete(child)
            elif isinstance(child, BridgeDomainObject): recursive_delete(child)
            elif isinstance(child, FilterEntryObject): recursive_delete(child)
            elif isinstance(child, SubjectObject): recursive_delete(child)
            elif isinstance(child, SubnetObject): recursive_delete(child)
            elif isinstance(child, AppProfileObject): recursive_delete(child)
            elif isinstance(child, EPGObject): recursive_delete(child)
        
        if isinstance(obj, FilterObject):
            if obj['dn'] not in flt_objs: object_delete(obj)
        elif isinstance(obj, ContractObject):
            if obj['dn'] not in ctr_objs: object_delete(obj)
        elif isinstance(obj, ContextObject):
            if obj['dn'] not in ctx_objs: object_delete(obj)
        elif isinstance(obj, L3OutObject):
            if obj['dn'] not in l3e_objs: object_delete(obj)
        elif isinstance(obj, FilterEntryObject):
            if obj['dn'] not in fe_objs: object_delete(obj)
        elif isinstance(obj, SubjectObject):
            if obj['dn'] not in sj_objs: object_delete(obj)
        elif isinstance(obj, BridgeDomainObject):
            if obj['dn'] not in bd_objs: object_delete(obj)
        elif isinstance(obj, AppProfileObject):
            if obj['dn'] not in ap_objs: object_delete(obj)
        elif isinstance(obj, SubnetObject):
            if obj['dn'] not in sn_objs: object_delete(obj)
        elif isinstance(obj, EPGObject):
            if obj['dn'] not in epg_objs: object_delete(obj)
    
    if not deploy_incremental:
        for tenant in tenant_list:
            try: tenant_obj = dom.Tenant(tenant['name'])
            except: continue
            recursive_delete(tenant_obj)
            if tenant['name'] in delete_tenants:
                object_delete(tenant_obj)
    
    dom.close()
    
    return {'Tenant' : tenant_objs.keys(),
            'Filter' : flt_objs.keys(),
            'Contract' : ctr_objs.keys(),
            'Context' : ctx_objs.keys(),
            'L3External' : l3e_objs.keys(),
            'BridgeDomain' : bd_objs.keys(),
            'FilterEntry' : fe_objs.keys(),
            'Subject' : sj_objs.keys(),
            'Subnet' : sn_objs.keys(),
            'AppProfile' : ap_objs.keys(),
            'EPG' : epg_objs.keys()}
