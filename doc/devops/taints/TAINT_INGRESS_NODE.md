# Steps 20.09.2025 DEV2

Taint node

    kubectl taint nodes ingress-pool-vsr4frizsr ingress-node=true:NoSchedule
    k describe nodes ingress-pool-vsr4frizsr

Apply test toleration

    k apply -f doc/devops/taints/echoserver_app_dev2_ingress_node.yaml
    # OK, Confirmed that pod echoserver-test-ingress-xxx is on ingress node

Add toleration to nginx - working approach

    cd doc/devops/taints
    kubectl patch daemonset  ingress-nginx-controller -n ingress-nginx --type merge --patch-file ingress_daemon_set_toleration.json

Add toleration to nginx - not working approach

    # push code changes with folder ionos_common/ingress_tainted
    k delete application ingress -n argocd
    k apply -f applications_dev2/infrastructure/ingress.yaml
    # check
    k get application -n argocd | grep ingress

# Steps 20.09.2025 SBX

    kubectl taint nodes ingress-pool-5k4ie6wngb ingress-node=true:NoSchedule
    k describe nodes ingress-pool-5k4ie6wngb
    cd doc/devops/taints
    kubectl patch daemonset  ingress-nginx-controller -n ingress-nginx --type merge --patch-file ingress_daemon_set_toleration.json
    # Manually delete remaining pods fron ingress node as for some reason they were not removed as on DEV2

# Steps 20.09.2025 PRD

    # try the different approach - first apply tollerations then taints (same effect)
    cd doc/devops/taints
    kubectl patch daemonset  ingress-nginx-controller -n ingress-nginx --type merge --patch-file ingress_daemon_set_toleration.json
    kubectl taint nodes ingress-pool-2-eykfqjfhfg ingress-node=true:NoSchedule
    k describe nodes ingress-pool-5k4ie6wngb

    # Manually delete remaining pods fron ingress node as for some reason they were not removed as on DEV2

# Taint Ingress Node - Archive notes

The purpose is to make all pods except for the ingress controller to be scheduled outside the ingress node.
So we need to taint the ingress node.

Folder ionos_common/ingress_tainted contains ingress controller definition with tolerations.
Changes cannot be done on existing ingress-controller. In case of issues it must be recreated.

Ingress node name: 

    │ ingress-pool-fbokxbh3hy

ingress-inginx pod:  

    ingress-nginx-controller-ss95b


Already has affinity:

    │ spec:                                                                                                                                                                                                                                                    │
    │   affinity:                                                                                                                                                                                                                                              │
    │     nodeAffinity:                                                                                                                                                                                                                                        │
    │       requiredDuringSchedulingIgnoredDuringExecution:                                                                                                                                                                                                    │
    │         nodeSelectorTerms:                                                                                                                                                                                                                               │
    │         - matchFields:                                                                                                                                                                                                                                   │
    │           - key: metadata.name                                                                                                                                                                                                                           │
    │             operator: In                                                                                                                                                                                                                                 │
    │             values:                                                                                                                                                                                                                                      │
    │             - ingress-pool-fbokxbh3hy

Add taint to the node

    kubectl taint nodes ingress-pool-fbokxbh3hy ingress-node=true:NoSchedule

Example pod definition with tolerations which means “This Pod can run on nodes that have the taint ingress-node=true:NoSchedule.”

    tolerations:
      - key: "ingress-node"
        operator: "Equal"
        value: "true"
        effect: "NoSchedule"

But probably better approach is to use nodeSelector and nodeAffinity.

# Node affinity

Node pool ingress-pool is meant for ingress-nginx controller. So it has label:

    --labels nodepool=ingress

See file doc/application_owners/INGRESS_NODE_SELECTOR_CONFIG.md

For all the nodes you need to define the pod so that it avoids the node with label:

    nodepool: ingress

    spec:
        affinity:
            nodeAffinity:
                requiredDuringSchedulingIgnoredDuringExecution:
                    nodeSelectorTerms:
                    - matchExpressions:
                      - key: nodepool
                          operator: NotIn
                          values:
                      - ingress

# Summary

- Use taints to make the node repel Pods.
- Use tolerations to let only the right Pods in.
- Use labels/affinity if you want to base it on Pod labels.
- Use admission controller (Kyverno/OPA) if you want it to depend on Pod annotations.

Steps for the future in case of issues:
1. Recreate ingress application using folder ionos_common/ingress_tainted.
2. Add taint to the node

   
    kubectl taint nodes ingress-pool-fbokxbh3hy ingress-node=true:NoSchedule



