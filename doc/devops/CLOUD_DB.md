# Cloud DB

Current recommendation on the DOME project is to use Cloud DB provided by Ionos.

## Setup
Cloud DB has been setup using the following commands:

### DEV2

    ionosctl lan create --datacenter-id 3e32e494-e3b5-4b8b-9947-1512079a467f --name dome-dev2-lan-2 --public=false
    ionosctl lan list --datacenter-id 3e32e494-e3b5-4b8b-9947-1512079a467f
    ionosctl k8s nodepool lan add --cluster-id 93d56451-f87c-4bf2-b097-33683e5886a4 --nodepool-id 4e2a4e82-23af-4ea7-a027-1d76ad04f376 --lan-id 3
    ionosctl k8s nodepool lan add --cluster-id 93d56451-f87c-4bf2-b097-33683e5886a4 --nodepool-id 28fb5e4b-82c3-4a47-904e-f99aaa7dd604 --lan-id 3

### DEV

    ionosctl lan create --datacenter-id f6a337d2-b356-4eb6-a6d2-00d2d42bd942 --name dome-dev-lan-2 --public=false
    ionosctl lan list --datacenter-id f6a337d2-b356-4eb6-a6d2-00d2d42bd942
    ionosctl k8s nodepool lan add --cluster-id d40d0a64-84ee-4384-a581-d6226a71a862 --nodepool-id d5be6a5b-b003-4403-a35e-c5535b158660 --lan-id 2
    ionosctl k8s nodepool lan add --cluster-id d40d0a64-84ee-4384-a581-d6226a71a862 --nodepool-id b67d5a00-2678-4746-941a-b2385703e79c --lan-id 2

### PRD

    ionosctl lan create --datacenter-id db088b6a-4c61-4a47-8fe9-a4f1c5f916cc --name dome-prd-lan-2 --public=false
    ionosctl k8s nodepool lan add --cluster-id 5821f7a6-e4ee-48c8-9404-741fc0ae281d --nodepool-id 8668accc-b521-4c57-a283-33907af85726 --lan-id 3
    ionosctl k8s nodepool lan add --cluster-id 5821f7a6-e4ee-48c8-9404-741fc0ae281d --nodepool-id 9188da94-d68b-4b5a-8e89-46c9516f518f --lan-id 3

Checks:

    ionosctl lan list --datacenter-id db088b6a-4c61-4a47-8fe9-a4f1c5f916cc
    ionosctl k8s nodepool list --cluster-id 5821f7a6-e4ee-48c8-9404-741fc0ae281d

## URLs
Due to security reasons Cloud DBs are available from their own clusters only via following URLs:

- SBX pg-75qkrjg6i4d7tlg2.postgresql.de-txl.ionos.com
- DEV pg-mlg52jm9egadod1s.postgresql.de-txl.ionos.com 
- DEV2 pg-7ibhgq9r54fl3acm.postgresql.de-txl.ionos.com
- PRD pg-3oc0026pnl3p1gi0.postgresql.de-fra.ionos.com 

## Database and user information

So far the following databases have been created:

DB name||Owner||SBX user||DEV2 user||DEV user||PRD user
postgres|karol.bialas@ionos.com|domesbx|domedev|domedev|domeprd
accessnode|domesupport@in2.es|desmosuser|desmosdevuser|desmosdevuser|desmosprduser
analyticsdb|georgios.peppas@eurodyn.com|analyticsdbuser|analyticsdevuser|N/A|analyticsprduser
supersetdb|georgios.peppas@eurodyn.com|supersetuser|supersetuser|N/A|N/A
sonarqubedb|alejandro.larios@inetum.com|sonarqubeuser|N/A|N/A|N/A
identity|miguel.mir@altia.es|alti4identity|N/A|N/A|N/A
ngb|nelsondavid.serna@bosonit.com|scorpiouser|scorpiouser|scorpiouser|scorpiouser