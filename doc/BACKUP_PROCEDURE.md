Open the ticket with request for backup.

Determine PODs and PVC you want to back up and list them in the ticket.
Label PVC you want to backup: data-wallet-postgres-0 backup=true
Annotate PODs you want to backup: backup.velero.io/backup-volumes=data

For example:

    kubectl label pvc data-wallet-postgres-0 backup=true -n in2 --overwrite
    kubectl annotate pod wallet-postgres-0 -n in2 backup.velero.io/backup-volumes=data

Ionos can assist you with labelling PVC.