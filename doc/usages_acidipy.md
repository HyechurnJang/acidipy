# Acidipy Library

## Object Inheritance & Reserved Actors

![Inheritance](Inheritance.png)

Actor : ACI Class operator with APIC Rest /api/node/class/~
Object : ACI Instance operator of Class with APIC Rest /api/mo/~

## Actor Abstraction

### AcidipyActor

**Reserved Name of Inherited Actor**

- Tenant
- Filter
- Contract
- Context
- L3External
- BridgeDomain
- AppProfile
- FilterEntry
- Subject
- Subnet
- EPG
- Endpoint
- Pod
- Node
- Paths
- VPaths
- Path

#### Retrive list of instance by actor name within parent's scope

Grammar : ActorName.**list()**

	def list(self, detail=False, sort=None, page=None, **clause)

Parameter
- detail
- sort
- page
- *clause*

*clause* : Input by key=value type or double pointed dict

Return : List of instance

#### Retrive a instance by target rn(Resource Name) within parent's scope

Grammar : ActorName**()**

	def __call__(self, rn, detail=False)
	
Parameter
- rn
- detail

Return : Target instance

#### Retrive counts by actor name within parent's scope

Grammar : ActorName.**count()**

	def count(self)

Return : Integer

### AcidipyActorHealth

#### Retrive list of health data by actor name within parent's scope

Grammar : ActorName.**health()**

	def health(self)

Return : List of health data

### AcidipyActorCreate

#### Create a instance by actor name within parent's scope

Grammar : ActorName.**create()**

	def create(self, **attributes)

Parameter
- *attributes*

*attributes* : Input by key=value type or double pointed dict

Return : Target instance created

### ControllerActor

**Reserved Name of Inherited Actor**

- Filter
- Contract
- Context
- L3External
- BridgeDomain
- AppProfile
- FilterEntry
- Subject
- Subnet
- EPG
- Endpoint
- Node
- Paths
- VPaths
- Path

#### Retrive list of instance by actor name

Grammar : ActorName.**list()**

	def list(self, detail=False, sort=None, page=None, **clause)

Parameter
- detail
- sort
- page
- *clause*

*clause* : Input by key=value type or double pointed dict

Return : List of instance

#### Retrive counts by actor name

Grammar : ActorName.**count()**

	def count(self)

Return : Integer

### ControllerActorHealth

#### Retrive list of health data by actor name

Grammar : ActorName.**health()**

	def health(self)

Return : List of health data

## Object Abstraction

### AcidipyObject

#### Get json format data

Grammar : Object.**toJson()**

	def toJson(self)

Return : Json string

#### Retrive detail data it self

Grammar : Object.**detail()**

	def detail(self)

Return : Object it self with detail data

### AcidipyObjectHealth

#### Retrive health data by object dn

Grammar : Object.**health()**

	def health(self)

Return : Object's health data

### AcidipyObjectModify

#### Update it self

Grammar : Object.**update()**

	def update(self)

Return : True of Exception

#### Delete it self

Grammar : Object.**delete()**

	def delete(self)

Return : True of Exception

### AcidipyObjectParent

#### Retrive parent object

Grammar : Object.**parent()**

	def parent(self, detail=False)

Return : Parent object

### AcidipyObjectChildren

#### Retrive list of children object

Grammar : Object.**children()**

	def children(self, detail=False, sort=None, page=None, **clause)

Parameter
- detail
- sort
- page
- *clause*

*clause* : Input by key=value type or double pointed dict

Return : Parent object

## Object Relation

Gramar : L3External_Object.**relate2Context()**

Gramar : BridgeDomain_Object.**relate2Context()**

Gramar : BridgeDomain_Object.**relate2L3External()**

Gramar : Subject_Object.**relate2Filter()**

Gramar : EPG_Object.**relate2BridgeDomain()**

Gramar : EPG_Object.**relate2Provider()**

Gramar : EPG_Object.**relate2Consumer()**

Gramar : EPG_Object.**relate2StaticPath()**







