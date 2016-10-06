# acidipy
Cisco ACI Python API

## Usages

### Import Source

	from apicipy import *

### Get Domain Session

	dom = Domain(<APIC_IP>, <USER>, <PASSWD>)

### Basic C.R.U.D

__Read Objects__

Reading name-only

> results = **OBJECT**.getList(dom)

	tenants = Tenant.getList(dom)

Reading with details

> results = **OBJECT**.getList(dom, detail=True)

	tenants = Tenant.getList(dom, detail=True)

Retrive details on a instance already read

> **OBJECT_INSTANCE**.getDetail()

	tenant_instance.getDetail()

__Create Object__

> object_instance = **OBJECT**(**PARAMETERS**)

	tenant_instance = Tenant(name="test_tenant")

__Update Object__

Update with **OBJECT**'s methods or .update()

> **OBJECT_INSTANCE**.**METHOD**(**PARAMETERS**)

	epg_instance.setBridgeDomain(bd_instance)

> **OBJECT_INSTANCE**["**OBJECT_ATTRIBUTE**"] = **DATA**

> **OBJECT_INSTANCE**.update()

	epg_instance["scope"] = bd_instance["scope"]
	epg_instance.update()

__Delete Object__

> **OBJECT_INSTANCE**.delete()

	tenant.delete()

