# acidipy
Cisco ACI Python API

**ACI** **D**eveloping **I**nterface for **PY**thon

version : 0.9 Beta

![Relations](./doc/object_relation.png)

## Support Object

**Prepared Objects**
| ACI Object Name | Acidipy Object Name | Description |
|-----------------|---------------------|-------------|
| fvTenant | TenantObject | Tenant |
| vzFilter | FilterObject | Filter |
| vzBrCP | ContractObject | Contract |
| fvCtx | ContextObject | Virtual Routing and Forwarding (VRF) |
| l3extOut | L3ExternalObject | L3 External |
| fvBD | BridgeDomainObject | Bridge Domain |
| fvAp | AppProfileObject | Appliation Profile |
| vzEntry | FilterEntryObject | Filter Entry |
| vzSubj | SubjectObject | Subject of Contract |
| fvSubnet | SubnetObject | Subnet |
| fvAEPg | EPGObject | Endpoint Group |
| fvCEp | EndpointObject | Endpoint |
| fabricPod | PodObject | Pod |
| fabricNode | NodeObject | ACI Node |
| fabricPathEpCont | PathsObject | Path Endpoint Container |
| fabricProtPathEpCont | VPathsObject | Protected Path Endpoint Container |
| fabricPathEp | PathObject | Path Endpoint |

**And Retrive Anything with Controller Object**

## Install

	$ install
	
Parameter
- -a : install ansible module
- -b : install binary tool
- -f : force install
- -r : remove acidipy & packages

## Example Acidipy

	import acidipy
	
	controller = acidipy.Controller('10.72.86.21', 'admin', '1234Qwer', False) # Get controller connection
	
	tenant = controller.Tenant.create(name='example-tenant') # Create tenant
	bd = tenant.BridgeDomain.create(name='example-bd') # Create bridge domain
	ap = tenant.AppProfile.create(name='example-ap') # Create application profile
	epg = ap.EPG.create(name='example-epg') # Create endpoint group
	epg.relate2BridgeDomain(bd) # Relate endpoint group to bridge domain
	
	print controller.Tenant.list() # Retrive list of tenant
	print tenant.AppProfile('example-ap').EPG.list() # Retrive list of endpoint group about tenant created
	print ap.EPG('example-epg') # Retrive endpoing group by name
	
	epg.delete() # Delete endpoint group
	ap.delete() # Delete application profile
	bd.delete() # Delete bridge domain
	tenant.delete() # Delete tenant
	
	controller.close() # Close controller connection

## Ansible Module

## Binary Tool



### Objects

- Domain
- Tenant
- Contact
- VRF
- BrDom
- AppProf
- Subnet
- EPG
- EP
- Pod
- Node
- Paths
- VPaths
- Path

### Methods

#### on Object's Method

##### Object.list()

Retrive list of Object

Parameter
- detail : retriving selection with name-only or full-data 
- sort : retriving sorting data
- page : retriving partial data
- clause : python style key=value parameters to use searching data matched

Return : List of Object's Instance

##### Object()

Retrive one Object pointed by dn

Parameter
- dn : target dn you want
- detail : retriving selection with name-only or full-data

Return : A Object's Instance

##### Object.count()

Retrive count of Object

Parameter : No

Return : Integer

##### Object.health()

Retrive health data of Object

Parameter : No

Return : List of Object's Health Instance

##### Object.create()



#### on Instance's Method



##### Instance.detail()

##### Instance.parent()

##### Instance.children()

##### Instance.health()

##### Instance.update()

##### Instance.delete()

##### Instance.relate2{Object}()








#### Class Method
- getList : Retrive Object List

#### Instance Method
- getDetail : Get all attributes on object retrived
- getRefresh : Get lastest attributes
- getParent : Get parent object
- getChildren : Get children objects
- create : Create object to APIC
- update : Update object to APIC
- delete : Delete object from APIC
- relate : Relate between objects
- << : c : as like create
- & : as like relate

## Usages

### Import Source

	from apicipy import *

### Get Domain Session

> **DOMAIN_INSTANCE** = **Domain**(**APIC_IP**, **USER**, **PASSWORD** [,debug(default:False)=True|False])

	domain_instance = Domain('123.123.123.123', 'cisco', 'cisco123')

### Basic C.R.U.D

#### Read Objects

Retrive name-only

> **OBJECT_INSTANCES** = **OBJECT**.getList(dom)

	tenant_instances = Tenant.getList(dom)

Retrive with details

> **OBJECT_INSTANCES** = **OBJECT**.getList(dom, detail=True)

	tenant_instances = Tenant.getList(dom, detail=True)

Retrive details on a instance already read

> **OBJECT_INSTANCE**.getDetail()

	tenant_instance.getDetail()

#### Create Object

Create Object Instance on Local

> **OBJECT_INSTANCE** = **OBJECT**(**PARAMETERS**)

	tenant_instance = Tenant(name='test_tenant')

Register Object to APIC with Object Instance's method create()

> **OBJECT_INSTANCE**.**create**(**PARENT_INSTANCE**)

	tenant_instance.create(domain_instance)
	
Or with "<<" Operator

> **PARENT_INSTANCE** **<<** **OBJECT_INSTANCE**

	domain_instance << tenant_instance

#### Update Object

Set Data to Object Instance

> **OBJECT_INSTANCE**["**OBJECT_ATTRIBUTE**"] = **DATA**

	epg_instance['scope'] = bd_instance['scope']

Update with Object Instance's method update()

> **OBJECT_INSTANCE**.**update**()
	
	epg_instance.update()

##### Relationship

Relate with Object Instance's method relate()

> **BIGGER_RELATION_INSTANCE**.**relate**(**SMALLER_RELATION_INSTANCE**)

	# as like BD(1) : EPG(N)
	epg_instance.relate(bd_instance)

Or with "&" Operator

> **RELATION_INSTANCE_1** **&** **RELATION_INSTANCE_2**

> **RELATION_INSTANCE_2** **&** **RELATION_INSTANCE_1**

	epg_instance & bd_instance
	bd_instance & epg_instance

#### Delete Object

Delete with Object Instance's method delete()

> **OBJECT_INSTANCE**.delete()

	tenant.delete()












