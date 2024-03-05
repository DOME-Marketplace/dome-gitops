# DOME-Marketplace GitOps

This repository contains the deployments and descriptions for the DOME-Marketplace. The development instance of the DOME-Marketplace runs on a managed kuberentes, provided by [Ionos](https://dcd.ionos.com).

A description of the deployed architecture and a description of the main flows inside the system can be found [here](./doc/ARCHITECTURE.md). The demo-scenario, show-casing some of the current features can be found under [demo](./doc/DEMO.md)

## Setup

The GitOps approach aims for a maximum of automation and will allow to reproduce the full setup. 
For more information about GitOps, see:
    - RedHat Pros and Cons - https://www.redhat.com/architect/gitops-implementation-patterns
    - ArgoCD - https://argo-cd.readthedocs.io/en/stable/
    - FluxCD - https://fluxcd.io/

### Preparation

> :warning: All documentation and tooling uses Linux and is only tested there(more specifically Ubuntu). If another system is used, please find proper replacements that fit your needs.

In order to setup the DOME-Marketplace, its recommended to install the following tools before starting

- [ionosctl-cli](https://github.com/ionos-cloud/ionosctl) to interact with the Ionos-APIs
- [jq](https://jqlang.github.io/jq/download/) as a json-processor to ease the work with the client outputs
- [kubectl](https://kubernetes.io/docs/tasks/tools/#kubectl) for debugging and inspecting the resources in the cluster
- [kubeseal](https://github.com/bitnami-labs/sealed-secrets#kubeseal) for sealing secrets using asymmetric cryptography

### Cluster creation

> :warning: The cluster is created on the Ionos-Cloud, therefor you should have your account data available.

1. In order to create the cluster, login to Ionos:
```shell
    ionosctl login 
```

2. A Datacenter as the logical bracket around the nodes in your cluster has to be created:
```shell
    export DOME_DATACENTER_ID=$(ionosctl datacenter create --name DOME-Marketplace -o json | jq -r '.items[0].id')
    # wait for the datacenter to be "AVAILABLE"
    watch ionosctl datacenter get -i $DOME_DATACENTER_ID
```

3. Create the Kubernetes Cluster and wait for it to be "ACTIVE":
```shell
    export DOME_K8S_CLUSTER_ID=$(ionosctl k8s cluster create --name DOME-Marketplace-K8S -o json | jq -r '.items[0].id')
    watch ionosctl k8s cluster get -i $DOME_K8S_CLUSTER_ID
```

4. Create the initial nodepool inside your cluster and datacenter:
```shell
    export DOME_K8S_DEFAULT_NODEPOOL_ID=$(ionosctl k8s nodepool create --cluster-id $DOME_K8S_CLUSTER_ID --name default-pool --node-count 2 --ram 8192 --storage-size 10 --datacenter-id $DOME_DATACENTER_ID --cpu-family "INTEL_SKYLAKE"  -o json | jq -r '.items[0].id')
    # wait for the pool to be available
    watch ionosctl k8s nodepool get --nodepool-id $DOME_K8S_DEFAULT_NODEPOOL_ID --cluster-id $DOME_K8S_CLUSTER_ID
```

5. Following the recommendations from the [Ionos-FAQ](https://docs.ionos.com/cloud/managed-services/managed-kubernetes/ingress-preserve-source-ip), we also dedicate a specific nodepool for the ingress-controller

```shell 
    export DOME_K8S_INGRESS_NODEPOOL_ID=$(ionosctl k8s nodepool create --cluster-id $DOME_K8S_CLUSTER_ID --name default-pool --node-count 1 --datacenter-id $DOME_DATACENTER_ID --cpu-family "INTEL_SKYLAKE" --labels nodepool=ingress -o json | jq -r '.items[0].id')
    # wait for the pool to be available
    watch ionosctl k8s nodepool get --nodepool-id $DOME_K8S_INGRESS_NODEPOOL_ID --cluster-id $DOME_K8S_CLUSTER_ID
```

6. Retrieve the kubeconfig to access the cluster:
```shell
    ionosctl k8s kubeconfig get --cluster-id $DOME_K8S_CLUSTER_ID > dome-k8s-config.json
    # Exporting the file path to $KUBECONFIG will make it the default config for kubectl. 
    # If you work with multiple clusters, either extend your existing config or use the file inline with the --kubeconfig flag.
    export KUBECONFIG=$(pwd)/dome-k8s-config.json
```


### Gitops Setup

> :bulb: Even thought the [cluster creation](#cluster-creation) was done on Ionos, the following steps apply to all [Kubernetes](https://kubernetes.io/) installations(tested version is 1.26.7). Its not required to use Ionos for that.


In order to provide GitOps capabilities, we use [ArgoCD](https://argo-cd.readthedocs.io/en/stable/). To setup the tool, we need 2 manual steps to deploy ArgoCD, as its decribed by the [manual](https://argo-cd.readthedocs.io/en/stable/getting_started/#1-install-argo-cd)
> :warning: The following steps expect kubectl to be already connected to the cluster, as described in [cluster-creationg step 6](#cluster-creation)  

1. Create a namespace for argocd. For easier configuration, we use argo's default ```argocd```
```shell
    kubectl create namespace argocd
```
2. Deploy argocd with extensions enabled:
```shell 
    kubectl apply -k ./extension/ -n argocd
```

From now on, every deployment should be managed by ArgoCD through [Applications](https://argo-cd.readthedocs.io/en/stable/core_concepts/).

### Namespaces

To properly seperate concerns, the first ```application``` to be deployed will be the [namespaces](./applications/namespaces.yaml). It will create all namespaces defined in the [ionos/namespaces folder](./ionos/namespaces/).

Apply the application via: 
```shell
    kubectl apply -f applications/namespaces.yaml -n argocd
    # wait for it to be SYNCED and Healthy
    watch kubectl get applications -n argocd
```

### Sealed Secrets

Using GitOps, means every deployed resource is represented in a git-repository. While this is not a problem for most resources, secrets need to be handled differently.
We use the [bitnami/sealed-secrets](https://github.com/bitnami-labs/sealed-secrets) project for that. It uses asymmetric cryptography for creating secrets and only decrypt them inside the cluster.
The sealed-secrets controller will be the first application deployed using ArgoCD. Since we want to use the [Helm-Charts](https://helm.sh/) and keep the values inside our git-repository, we get the problem of 
ArgoCD [only supporting values-files inside the same repository as the chart](https://argo-cd.readthedocs.io/en/stable/user-guide/helm/#values-files)(as of now, there is an open PR to add that functionality -> [PR#8322](https://github.com/argoproj/argo-cd/pull/8322) ). 
In order to workaround that shortcomming, we are using "wrapper charts". A wrapper-chart does consist of a [Chart.yaml](https://helm.sh/docs/topics/charts/#the-chartyaml-file) with a dependency to the actual chart. Besides that, we have a [values.yaml](https://helm.sh/docs/chart_template_guide/values_files/) with our specific overrides.
See the [sealed-secrets folder](./ionos/sealed-secrets) as an example.


Apply the application via: 
```shell
    kubectl apply -f applications/sealed-secrets.yaml -n argocd
    # wait for it to be SYNCED and Healthy
    watch kubectl get applications -n argocd
```

Once its deployed, secrets can be "sealed" via:

```bash
    kubeseal -f mysecret.yaml -w mysealedsecret.yaml --controller-namespace sealed-secrets  --controller-name sealed-secrets
```

### Ingress controller

In order to access applications inside the cluster, an [Ingress-Controller](https://kubernetes.io/docs/concepts/services-networking/ingress-controllers/) is required. We use the [NGINX-Ingress-Controller](https://github.com/kubernetes/ingress-nginx) here. 

> The configuration expects a nodepool labeld with ```ingress``` in order to safe IP addresses. If you followed [cluster-creation](#cluster-creation) such pool already exists. 

Apply the application via: 
```shell
    kubectl apply -f applications/ingress.yaml -n argocd
    # wait for it to be SYNCED and Healthy
    watch kubectl get applications -n argocd
```

### External-DNS

In order to automatically create DNS entries for [Ingress-Resources](https://kubernetes.io/docs/concepts/services-networking/ingress/), [External-DNS](https://github.com/kubernetes-sigs/external-dns) is used.

> :bulb: The ```dome-marketplace.org|io|eu|com``` domains are currently using nameservers provided by AWS Route53. If you manage the domains somewhere else, follow the recommendations in the [External-DNS documentation](https://github.com/kubernetes-sigs/external-dns/tree/master/docs/tutorials).

1. External-DNS watches the ingress objects and creates A-Records for them. To do so, it needs the ability to access the AWS APIs. 
    1. Create the IAM Policy accoring to the [documentation](https://github.com/kubernetes-sigs/external-dns/blob/master/docs/tutorials/aws.md#iam-policy)
    2. Create a user in AWS IAM and assign the policy. 
    3. Create an access key and store it in a file of format:
```txt
    [default]
    aws_secret_access_key = THE_KEY
    aws_access_key_id = THE_KEY_ID
```
    4. Base64 encode the file and put it into a secret of the following format:
```yaml
    apiVersion: v1
kind: Secret
metadata:
  name: aws-access-key
  namespace: infra
data:
  credentials: W2RlZmF1bHRdCmF3c19zZWNyZXRfYWNjZXNzX2tleSA9IFRIRV9LRVkKYXdzX2FjY2Vzc19rZXlfaWQgPSBUSEVfS0VZX0lE
```
    5. Seal the secret and commit the sealed secret. :warning: Never put the plain secret into git.

2. Apply the application: 
```shell
    kubectl apply -f applications/external-dns.yaml -n argocd
    # wait for it to be SYNCED and Healthy
    watch kubectl get applications -n argocd
```

### Cert-Manager

In addition to the dns-entries, we also need valid certificates for the ingress. The certificates will be provided by [Lets encrypt](https://letsencrypt.org/). To automate creation and update of the certificates, [Cert-Manager](https://cert-manager.io/) is used. 

1. In order to follow the [ACME protocol](https://datatracker.ietf.org/doc/html/rfc8555), Cert-Manager also needs the ability to create proper DNS entries. Therefor we have to provide the AWS account used by [External-DNS](#external-dns), too. 
    1. Put key and key-id into the following template:
```yaml
    apiVersion: v1
    kind: Secret
    metadata:
        name: aws-access-key
        namespace: cert-manager
    stringData:
        key: "THE_KEY"
        keyId: "THE_KEY_ID"
```
    2. Seal the secret and commit the sealed secret. :warning: Never put the plain secret into git.

2. Update the [issuer](./ionos/cert-manager/templates/issuer.yaml) with information about the hosted zone managing your domain and commit it.
3. Apply the application: 
```shell
    kubectl apply -f applications/cert-manager.yaml -n argocd
    # wait for it to be SYNCED and Healthy
    watch kubectl get applications -n argocd
```

### Update ArgoCD

ArgoCD provides a nice [GUI](argocd.dome-marketplace.org) and a [command-line tool](https://argo-cd.readthedocs.io/en/stable/getting_started/#2-download-argo-cd-cli) to support the deployments. In order for them to work properly, an ingress and auth-mechanism need to be configured.

#### Ingress

Since ArgoCD is already running, we also use it to extend it self, by just providing an [ingress-resource](./ionos/argocd/ingress.yaml) pointing towards its server. That way, we will get a proper URL automatically throught the previously configured [External-DNS](#external-dns) and [Cert-Manager](#cert-manager).

#### Auth

To seamlessly use ArgoCD, we use [Githubs Oauth](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps) to manage users for ArgoCd together with those accessing the repo. 
1. Register ArgoCd in Github, following the [documentation](https://argo-cd.readthedocs.io/en/stable/operator-manual/user-management/#1-register-the-application-in-the-identity-provider)
2. Put the secret into:
```yaml
    apiVersion: v1
    kind: Secret
    metadata:
    labels:
        app.kubernetes.io/part-of: argocd
    name: github-secret
    namespace: argocd
    stringData: 
    clientSecret: THE_CLIENT_SECRET
```
3. Seal and commit it.
4. Configure the organizations to be allowed in the [configmap](./ionos/argocd/configmap.yaml)
5. Configure user-roles in the [rbac-configmap](./ionos/argocd/configmap-rbac.yaml)
6. Apply the application 
```shell
    kubectl apply -f applications/argocd.yaml -n argocd
    # wait for it to be SYNCED and Healthy
    watch kubectl get applications -n argocd
```

Login to our [ArgoCD](https://argocd.dome-marketplace.org).

## Deploy a new application

In order to deploy a new application, follow the steps:
1. Fork the repository and create a new branch.
2. (OPTIONAL) Add a new namespace to the [namespaces](./ionos/namespaces/)
3. Add either the helm-chart(see [External-DNS](./ionos/external-dns/) as an example) or the plain manifests(see [ArgoCD](./ionos/argocd/) as an example) to a properly namend folder under [/ionos](/ionos/)
4. Add your application to the [/applications](./applications/) folder.
5. Create a PR and wait for it to be merged. The application will be automatically deployed afterwards.

For a detailed guide on how to deploy a new application, you can refer to the [Integration Guide](./doc/INTEGRATION.md)

## Blue-Green Deployments

In order to reduce the resource-usage and the number of deployments to maintain, the cluster supports [Blue-Green Deployments](https://www.redhat.com/en/topics/devops/what-is-blue-green-deployment).
To integrate seamless with ArgoCD, the extension [Argo Rollouts](https://argo-rollouts.readthedocs.io/en/stable/) is used. The standard ArgoCD installation is extended via the [argo-rollouts.yaml](./ionos/argocd/argo-rollouts.yaml), the [configmap-cmd.yaml](./ionos/argocd/configmap-cmd.yaml) and the [dashboard-extension.yaml](./ionos/argocd/dashboard-extension.yaml)(to integrate with the ArgoCD dashboard). 

Blue-Green Deployments on the cluster will be done through two mechanisms:

- the [rollout-injecting-webhook](https://github.com/wistefan/rollout-injecting-webhook) automatically creates a [Rollout](https://argo-rollouts.readthedocs.io/en/stable/features/specification/) for each deployment in enabled workspaces(currently "marketplace", see [rollout-webhook deployment](./ionos/marketplace/rollout-webhook/)) - read the [doc](https://github.com/wistefan/rollout-injecting-webhook/blob/main/README.md) for more information
- explicitly creating Rollout-Specs(see the [official documentation](https://argo-rollouts.readthedocs.io/en/stable/features/specification/))

> :warning: Be aware how Blue-Green Rollouts work and there limitations. Since they create a second instance of the application, this is only suitable for stateless-applications(as a Deployment-Resource should be). Stateful-Applications can lead to bad results like deadlocks. If the applications takes care of Datamigrations, configure it to not migrate before Promotion and connect the new revision to another database. To disable the [Rollout-Injection](https://github.com/wistefan/rollout-injecting-webhook), annotate the deployment with ```wistefan/rollout-injecting-webhook: ignore```

