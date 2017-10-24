# acidipy
Cisco ACI Python API

**ACI** **D**eveloping **I**nterface for **PY**thon

version : 0.12.1

last change : jzlib & bug fix

![Relations](./doc/Relation.png)

## Support Object

**Prepared Objects**

| ACI Object Name | Acidipy Object Name | Reserved Code Name | Description |
|-----------------|---------------------|--------------------|-------------|
| fvTenant | aciTenantModel | Tenant | Tenant |
| fvCtx | aciContextModel | Context | Virtual Routing and Forwarding (VRF) |
| fvBD | aciBridgeDomainModel | BridgeDomain | Bridge Domain |
| fvAp | aciAppProfileModel | AppProfile | Appliation Profile |
| fvSubnet | aciSubnetModel | Subnet | Subnet |
| fvAEPg | aciEPGModel | EPG | Endpoint Group |
| fvCEp | aciEndpointModel | Endpoint | Endpoint |
| fabricPod | aciPodModel | Pod | Pod |
| fabricNode | aciNodeModel | Node | ACI Node |
| fabricPathEpCont | aciPathsModel | Paths | Path Endpoint Container |
| fabricProtPathEpCont | aciVPathsModel | VPaths | Protected Path Endpoint Container |
| fabricPathEp | aciPathModel | Path | Path Endpoint |
| vzFilter | aciFilterModel | Filter | Filter |
| vzBrCP | aciContractModel | Contract | Contract |
| vzEntry | aciFilterEntryModel | FilterEntry | Filter Entry |
| vzSubj | aciSubjectModel | Subject | Subject of Contract |
| l3extOut | aciL3OutModel | L3Out | L3 External Out |
| l3extInstP | aciL3ProfileModel | L3Profile | L3 External Profile |
| topSystem | aciSystemModel | System | Node System Details |
| l1PhysIf | aciPhysIfModel | PhysIf | Physical Interfaces |

**And Retrieve Anything with Controller Object through "Class()" Method**

## Install

**From GIT**

	$ python setup.py build
	$ python setup.py install

**From PIP**

	$ pip install acidipy

## Example Acidipy

	import acidipy
	
	controller = acidipy.Controller('xxx.xxx.xxx.xxx', 'admin', '1234Qwer') # Get controller connection
	
	tenant = controller.Tenant.create(name='example-tenant') # Create tenant
	bd = tenant.BridgeDomain.create(name='example-bd') # Create bridge domain
	ap = tenant.AppProfile.create(name='example-ap') # Create application profile
	epg = ap.EPG.create(name='example-epg') # Create endpoint group
	
	epg.relate(bd) # Relate endpoint group to bridge domain
	
	print controller.Tenant.list() # Retrive list of tenant
	print tenant.AppProfile('example-ap').EPG.list() # Retrive list of endpoint group about tenant created
	print ap.EPG('example-epg') # Retrive endpoing group by name
	
	print ap.parent() # Retrive example-ap's parent
	print ap.children() # Retrive example-ap's children
	print ap.detail() # Retrive example-ap's whole attributes
	
	epg.delete() # Delete endpoint group
	ap.delete() # Delete application profile
	bd.delete() # Delete bridge domain
	tenant.delete() # Delete tenant
	
	controller.close() # Close controller connection

## Usages

see Acidipy Library [here](doc/usages_acidipy.md)

see Ansible Module [here](doc/usages_ansible.md)

see Binary Tools [here](doc/usages_bintools.md)
