
## Prep

- get the kubeconfig from https://dcd.ionos.com/latest/ for FF_DOME_POC
- install ionosctl -> [ionosctl-cli on github](https://github.com/ionos-cloud/ionosctl)
- install jq ->  [jq on github](https://jqlang.github.io/jq/download/)
- install helm -> [helm.sh install](https://helm.sh/docs/intro/install/)

## Gitops Setup

- ```kubectl create namespace argocd```
- ```kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml```

## Sealed Secrets

Seal secrets before adding them to the cluster:
```bash
    kubeseal <SECRET_FILE >OUTPUT_FILE -o yaml --controller-namespace sealed-secrets  --controller-name sealed-secrets 
```


## Ingress controller

> nginx is used, since its documented in the ionos FAQ -> we just follow the recommendation for [ingress](https://docs.ionos.com/cloud/managed-services/managed-kubernetes/ingress-preserve-source-ip)

- get the cluster id for the dome poc
```bash
    export DOME_CLUSTER=$(ionosctl k8s cluster list -o json  | jq -r '.items[] | select(.properties.name =="FF_DOME_POC").id') 
```
- get the datacenter id for DOME Demo 
```bash
    export DOME_DATACENTER=$( ionosctl datacenter list -o json | jq -r '.items[] | select(.properties.name =="FF DOME Demo").id')
```
- create a nodepool for the ingress controller
```bash
    ionosctl k8s nodepool create --cluster-id $DOME_CLUSTER \
    --name ingress --node-count 1 --datacenter-id $DOME_DATACENTER --labels nodepool=ingress --cpu-family "INTEL_SKYLAKE"
```
- wait until the nodepool is "ACTIVE"
```bash
    ionosctl k8s nodepool list --cluster-id $DOME_CLUSTER -o json  | jq '.items[] | select(.properties.name=="ingress").metadata.state'
```
- install the nginx-ingress controller with the [values.yaml](./ionos/ingress/values.yaml) from the ingress folder
```bash
    helm upgrade --install ingress-nginx ingress-nginx \
    --repo https://kubernetes.github.io/ingress-nginx \
    --namespace ingress-nginx --create-namespace -f ./ionos/ingress/values.yaml \
    --version 4.7.2
```

## Cert-Manager

- install CRDs
```bash
    kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.12.4/cert-manager.crds.yaml
```

- install cert-manager 
```
helm install \
    cert-manager jetstack/cert-manager \
    --namespace cert-manager \
    --create-namespace \
    --version v1.12.4
```