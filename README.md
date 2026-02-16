# DOME-Marketplace GitOps

## Scope of the document
This repository contains the deployments and descriptions for the DOME-Marketplace. The development instance of the DOME-Marketplace runs on a managed kubernetes, provided by [Ionos](https://dcd.ionos.com).

A description of the deployed architecture and a description of the main flows inside the system can be found [here](./doc/ARCHITECTURE.md).

## Setup

The GitOps approach aims for a maximum of automation and will allow to reproduce the full setup. 
For more information about GitOps, see:
    - RedHat Pros and Cons - https://www.redhat.com/architect/gitops-implementation-patterns
    - ArgoCD - https://argo-cd.readthedocs.io/en/stable/
    - FluxCD - https://fluxcd.io/

### Preparation

> :warning: All documentation and tools use Linux and are tested exclusively on that platform (specifically Ubuntu). If you are using a different system, please ensure you find suitable replacements that meet your requirements.

In order to setup the DOME-Marketplace, its recommended to install the following tools before starting

- [ionosctl-cli](https://github.com/ionos-cloud/ionosctl) to interact with the Ionos-APIs
- [jq](https://jqlang.github.io/jq/download/) as a json-processor to ease the work with the client outputs
- [kubectl](https://kubernetes.io/docs/tasks/tools/#kubectl) for debugging and inspecting the resources in the cluster
- [kubeseal](https://github.com/bitnami-labs/sealed-secrets#kubeseal) for sealing secrets using asymmetric cryptography


### Gitops Setup

> :bulb: Even thought the [cluster creation](#cluster-creation) was done on Ionos, the following steps apply to all [Kubernetes](https://kubernetes.io/) installations (tested version is 1.26.7). Its not required to use Ionos for that.

In order to provide GitOps capabilities, we use [ArgoCD](https://argo-cd.readthedocs.io/en/stable/). To setup the tool, we use ArgoCD helm [chart](https://github.com/argoproj/argo-helm/tree/main/charts/argo-cd).

### Configuration of `kubectl` to access the remote cluster
Before starting the integration process, the team has to configure **kubectl** in order to access the remote cluster locally following the steps described below.
1. **Request** the cluster administrator to create a service account, providing the name of your organization and the namespace within which your application will be deployed. You will be provided with a configuration file to access the cluster;
2. **modify** the **KUBECONFIG** environment variable by adding the path to the configuration file;
3. **verify** that the new context has been added by executing the following command
```bash
	kubectl config get-contexts
```
4. switch the context by executing the following command:
```
kubectl config use-context <name of the context>
```

After these steps, the team is able to run `kubectl` commands on the remote cluster.
The team must ensure that the username of the new context is **unique** across all contexts. If the username is already in use, the developer must update it in the configuration file.
The associated service account operates with limited permissions, allowing view access to all namespace resources but write access exclusively to secrets.  

### Repository structure
Team members begin by forking the main GitOps repository and creating a new branch for their specific integration work. This facilitates isolated development and changes.

The GitOps repository has the following structure:
```
.github/
   └── CODEOWNERS
   └── workflows/
applications_sbx/
   └── app_1/
	   └── app_1.yaml
   └── app_2/
		└── app_2.yaml
   . . .
applications_dev/
   └── app_1/
	   └── app_1.yaml
   └── app_2/
		└── app_2.yaml
   . . .
applications_dev2/
   └── app_1/
	   └── app_1.yaml
   └── app_2/
		└── app_2.yaml
   . . .
applications_prd/
   └── app_1/
	   └── app_1.yaml
   └── app_2/
		└── app_2.yaml
   . . .
doc/
   └── application_owners/
   └── devops/
   └── external-dns-ionos-webhook/
   └── img/   
   └── ARCHITECTURE.md 
   . . .
ionos_sbx/
   └── app_1/
         └── Chart.yaml
         └── values.yaml
         . . .
ionos_dev/
   └── app_1/
         └── Chart.yaml
         └── values.yaml
         . . .
ionos_dev2/
   └── app_1/
         └── Chart.yaml
         └── values.yaml
         . . .
ionos_prd/
   └── app_1/
         └── Chart.yaml
         └── values.yaml
```

For each environment, two main directories are defined:
- `applications_<env>`: it will host the environment-specific ArgoCD applications;
- `ionos_<env>`: it will host application's manifest files;

### DevOps Methodologies

This section explains the application owners how to deploy an application into the DOME repository.
The development workflow relies on two distinct but integrated enviroments: the version control system on **GitHub** for code management and the **ticketing platform** for task tracking.
Although the ticketing system operates _outside_ the direct scope of the automated DevOps pipeline, it plays a critical role in **monitoring development activities**. Therefore, developers **are required to** adhere to a dual-step process: opening a tracking ticket to define the scope of work, followed by the creation of a Pull Request on GitHub. This practice ensures that all modifications are properly cataloged and auditable.
The operations every application owner **must** follow are described below.

1. **Ownership & Traceability through the CODEOWNERS file**
To ensure clear accountability from the start, make sure that your GitHub username is added to the `CODEOWNERS` file, linked [here](https://github.com/DOME-Marketplace/dome-gitops/blob/main/.github/CODEOWNERS).

2. **Integration Pipeline**
The team intending to integrate its component on DOME needs to adhere to a structured set of steps, which vary depending on wheter it is an initial release or a subsequent update.

If the application if being deployed **for the first time**, the steps are:
1. **fork** the repository and **create** a new branch;
2. **add** component manifest file;
3. **add** ArgoCD application;
4. **create** a Pull Request and a related ticket on the ticketing system.

If the application **has alreeady been deployed**, the steps are:
1. **fork** the repository and **create** a new branch;
2. **update** component manifest file;
3. **create** a Pull Request and a related ticket on the ticketing system

Further informations about the deploy procedure are explained in the INTEGRATION file, linked [here](https://github.com/DOME-Marketplace/dome-gitops/blob/main/doc/application_owners/INTEGRATION.md).

3. **Create a ticket on the Ticketing System**
In order to approve and merge your PR you have to create a new ticket on the **DOME Ticketing System**, which can be found [here](https://ticketing-int.dome-marketplace.eu/).

The steps to create a new ticket related to your PR are the followings.
1. The category "13 – DevOps Deployment" must be selected;
2. It is mandatory to classify the request using the specific "Problem Typology" corresponding to the affected environment:
	**01 – PR SBX:** This code refers to issues occurring in the Prototyping environment;
	**02 – PR DEV:** This code refers to issues occurring in the Pre-Production environment;
	**03 – PR PROD:** This code refers to issues occurring in the Production environment;
	**04 – New deployment environment request:** This category is used to request the setup of a new environment.
3. Insert the name of both the environment and the component you are requesting the update;
4. Put the link of your PR on the ticket.

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

> The configuration expects a nodepool labeld with `ingress` in order to safe IP addresses. If you followed [cluster-creation](#cluster-creation) such pool already exists. 

Apply the application via: 
```shell
    kubectl apply -f applications/ingress.yaml -n argocd
    # wait for it to be SYNCED and Healthy
    watch kubectl get applications -n argocd
```

## External-DNS

In order to automatically create DNS entries for [Ingress-Resources](https://kubernetes.io/docs/concepts/services-networking/ingress/), [External-DNS](https://github.com/kubernetes-sigs/external-dns) is used.

> :bulb: The `dome-marketplace.org|io|eu|com` domains are currently using nameservers provided by AWS Route53. If you manage the domains somewhere else, follow the recommendations in the [External-DNS documentation](https://github.com/kubernetes-sigs/external-dns/tree/master/docs/tutorials).

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