# Create and bind LAN (DEV2)

    ionosctl lan create --datacenter-id 3e32e494-e3b5-4b8b-9947-1512079a467f --name dome-dev2-lan-2 --public=false
    ionosctl lan list --datacenter-id 3e32e494-e3b5-4b8b-9947-1512079a467f

    ionosctl k8s nodepool lan add --cluster-id 93d56451-f87c-4bf2-b097-33683e5886a4 --nodepool-id 4e2a4e82-23af-4ea7-a027-1d76ad04f376 --lan-id 3
    ionosctl k8s nodepool lan add --cluster-id 93d56451-f87c-4bf2-b097-33683e5886a4 --nodepool-id 28fb5e4b-82c3-4a47-904e-f99aaa7dd604 --lan-id 3

# Create and bind LAN (DEV)

    ionosctl lan create --datacenter-id f6a337d2-b356-4eb6-a6d2-00d2d42bd942 --name dome-dev-lan-2 --public=false
    ionosctl lan list --datacenter-id f6a337d2-b356-4eb6-a6d2-00d2d42bd942
    # ionosctl k8s nodepool list --cluster-id d40d0a64-84ee-4384-a581-d6226a71a862
    ionosctl k8s nodepool lan add --cluster-id d40d0a64-84ee-4384-a581-d6226a71a862 --nodepool-id d5be6a5b-b003-4403-a35e-c5535b158660 --lan-id 2
    ionosctl k8s nodepool lan add --cluster-id d40d0a64-84ee-4384-a581-d6226a71a862 --nodepool-id b67d5a00-2678-4746-941a-b2385703e79c --lan-id 2

# Create and bind LAN (PRD)

    ionosctl lan create --datacenter-id db088b6a-4c61-4a47-8fe9-a4f1c5f916cc --name dome-prd-lan-2 --public=false
    ionosctl lan list --datacenter-id db088b6a-4c61-4a47-8fe9-a4f1c5f916cc
    # ionosctl k8s nodepool list --cluster-id 5821f7a6-e4ee-48c8-9404-741fc0ae281d
    ionosctl k8s nodepool lan add --cluster-id 5821f7a6-e4ee-48c8-9404-741fc0ae281d --nodepool-id 8668accc-b521-4c57-a283-33907af85726 --lan-id 3
    ionosctl k8s nodepool lan add --cluster-id 5821f7a6-e4ee-48c8-9404-741fc0ae281d --nodepool-id 9188da94-d68b-4b5a-8e89-46c9516f518f --lan-id 3