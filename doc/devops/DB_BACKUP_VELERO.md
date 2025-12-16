# Backup of data with Velero

Velero serves as a utility for managing the backup and restoration of Kubernetes cluster resources and persistent volumes. It interacts with the Kubernetes API to capture the state of objects and stores the backup data in an external object storage service (e.g., S3 buckets). This tool is essential for cluster migration and recovering from system outages.

## Introduction
Velero is currently using Ionos 3 S3 bucket for backup - one per environment:
- dome-backup-sbx
- dome-backup-dev2
- dome-backup-prd

It has been installed using helm chart **vmware-tanzu/velero** on namespace _velero_
Velero client
It’s recommended to install velero client for accessing velero information on backups and restoration.
Client can be installed with:

    wget https://github.com/vmware-tanzu/velero/releases/download/v1.15.2/velero-v1.15.2-darwin-amd64.tar.gz
    tar -xvf velero-v1.15.2-darwin-amd64.tar.gz -C velero-client

On mac:

    brew install velero

Velero client test:

    velero version

## Scope
Currently Velero is configured to scan the following namespaces for backup
- in2
- zammad
- knowledgebase
- cs-identity
- marketplace

Exact list of pods subject to backup can be obtained with command

    kubectl get pods -A -o json | jq '.items[] | select((.metadata.annotations["backup.velero.io/backup-volumes"] // "") != "") | .metadata.namespace + "/" +.metadata.name'

As for November 2025 the following pods are subject to backup:

IN2:
- data-wallet-postgres-0
- data-dome-wallet-keycloak-postgres-0
- data-wallet-vault-server

ZAMMAD:
- zammad-postgresql-0
- zammad2-postgresql-0
  KNOWLEDGEBASE:
- bookstack-xxxxxxxxxx-xxxxx
- mysql-knowledgebase-0

CS_IDENTITY:
- cs-identity-postgresql-0

MARKETPLACE:
- mysql-til-0

## Schedules
Velero is using 2 schedules per environment:
- daily (TTL 168h)
- hourly  (TTL 5h)

Details on schedules can be retrieved with command:

    kubectl get schedule -n velero

## Backup procedure
1. Open the ticket with a request for backup.
2. Determine PODs and PVC you want to back up and list them in the ticket.
3. Label PVC you want to backup: data-wallet-postgres-0 backup=true
4. Annotate PODs you want to backup: backup.velero.io/backup-volumes=data

For example:

    kubectl label pvc data-wallet-postgres-0 backup=true -n in2 --overwrite
    kubectl annotate pod wallet-postgres-0 -n in2 backup.velero.io/backup-volumes=data

Please note that those changes should not be done from within the cluster level (manually) but by modification of GitOps repo resources so that changes are persistent after pods get recreated.

## Backup restoration
Each backup execution results in ‘backup’ resource being created in the cluster.
Backups can be listed using command:

    kubectl get backup -n velero
To get more details on specific backup:

    velero backup describe $backup-id  --details

Backup restoration requires determination backup item running the command:

    velero restore create --from-backup $backup-id
For example:

    velero restore create --from-backup schedule-dev2-daily-20250730030010
Each backup restoration produces ‘restore’ resource item with details on restoration process and result:

    velero restore get
