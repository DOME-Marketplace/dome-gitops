# Integration of a new application

The following documentation describes the integration approach designed for DOME. The team intending to integrate its component needs to adhere to a structured set of steps:

1. [Create a new branch on the repository](#step-1-create-a-new-branch-on-the-repository)
2. [Add a new namespace](#step-2-add-a-new-namespace)
3. [Add component manifest files](#step-3-add-component-manifest-files)
4. [Add ArgoCD application](#step-4-add-argocd-application)
5. [Create a Pull Request and wait for merge](#step-5-create-a-pull-request)

The following paragraphs detail the steps to integrate a new application into DOME.

## Step 0: Configuration of kubectl to access the remote cluster

Before starting the integration process, you need to configure [**kubectl**](https://kubernetes.io/docs/tasks/tools) in order to access the remote cluster locally; to do this, follow the steps below:

1. Request the cluster administrator to create a service account, providing the name of your organization and the namespace within which your application will be deployed. You will be provided with a configuration file to access the cluster
2. Modify the **KUBECONFIG** environment variable by adding the path to the configuration file
3. Verify that the new context has been added by executing the following command:

```sh
kubectl config get-contexts
```

4. Switch the context by executing the following command:

```sh
kubectl config use-context <name of the context>
```

At this point, you should be able to run kubectl commands on the remote cluster.

> ⚠️ Ensure that the user name of the new context has not already been used in other contexts; if so, modify the user name in the configuration file.

> ⚠️The service account provided to you will have limited permissions; you will be able to view all resources within your namespace but will only have write access to secrets.

## Step 1: Create a new branch on the repository

Team members begin by creating a new branch from GitOps repository main branch, with the name starting with the **enviroment name** 
Ex: sbx-myapp-first-deploy, and working there for their specific integration work. This facilitates tracking activities, changes, and clear visibilty by DevOps team.

> ⚠️ If you are not part of the Dome Organization you will not able to create branch on the Dome Repository, please contact Paolo Fabriani, or DevOps team in order to get the relative access.

After cloning the project, navigate to the project directory to proceed with the rest of the guide.

### Repository structure
The GitOps repository has the following structure:

```
applications_sbx/
  └── infrastructure
    └── argocd.yaml
    ...
  └──  marketplace
    └── access-node.yaml
    ...
  └── infrastructure.yaml
  └── marketplace.yaml
  └── release1
    └──  owner or namespace
      └──  app_1.yaml
      └──  app_2.yaml
  ...
ionos_sbx/
  └── app_1/
    └── Chart.yaml
    └── values.yaml
  └── app_2/
    └── deployment.yaml
    └── service.yaml
    └── ingress.yaml
    └── secret.yaml
    └── configmap.yaml
  ...
```

For each environment, two directories are defined:

- ```applications_<env>```: it will host the environment-specific Argocd applications (see [Add ArgoCD application](#step-4-add-argocd-application))
- ```ionos_<env>```: it will host application manifest files (see [Add component manifest files](#step-3-add-component-manifest-files))

> ⚠️ The ```applications``` and ```ionos``` directories are currently reserved for the demo environment. For the continuation of the guide, we will use the ```sbx``` environment, which serves as a playground where teams can test the integration of their components within the DOME ecosystem.

## Step 2: Add a new namespace (if not exists)
Each application is deployed to a separate namespace. To create the namespace for your application, follow these steps:

1. Move to the namespace directory:

```sh
cd ionos_sbx/namespaces
```

2. Create a manifest file for your app namespace:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: <app namespace>
```

## Step 3: Add component manifest files
The team incorporates their integration by adding either a Helm chart or plain Kubernetes manifests to a properly named folder under the designated directory. This directory serves as a centralised location for all integrations.

First, create a directory for your application by executing the following commands:

```sh
cd ionos_sbx/
mkdir <name of you application>
```

Then put your application manifest files or Helm charts inside this directory. Once done, the structure should look like the following:

```
ionos_sbx/
  └── your-app/
    └── deployment.yaml
    └── service.yaml
    └── ingress.yaml
    └── secret.yaml
    └── configmap.yaml
```

or, if you are using Helm:

```
ionos_sbx/
  └── your-app/
    └── templates/
      └── secret.yaml
      └── configmap.yaml 
    └── Chart.yaml
    └── values.yaml
```

> You don't have manifest files nor Helm charts? Follow this [guide](./K8S_APPLICATION.md).

### Add secrets
Using GitOps, means every deployed resource is represented in a git-repository. While this is not a problem for most resources, secrets need to be handled differently. We use the [bitnami/sealed-secrets](https://github.com/bitnami-labs/sealed-secrets) project for that. 

To encrypt secrets from your local machine to the remote cluster, it is necessary to [install kubeseal](https://github.com/bitnami-labs/sealed-secrets?tab=readme-ov-file#kubeseal). Once installed, you can create an encrypted secret as follows:

1. Create a plain secret manifest file named ```<secret name>-plain-secret.yaml``` (**IMPORTANT**: Make sure the file name ends with ```-plain-secret.yaml``` so it will be ignored when pushing to repository)

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: <secret name>
  namespace: <app namespace>
data: 
  <key>: <base64 encoded value>
```

2. Seal the secret by running the following command:

```sh
kubeseal -f <secret name>-plain-secret.yaml -w <secret name>-sealed-secret.yaml --controller-namespace sealed-secrets --controller-name sealed-secrets
```

or using the script SealSecret:

**Windows PowerShell**

```shell
.\scripts\SealSecret.ps1 -secretPath <path to plain secret>
```

**Shell**

```shell
# chmod +x ./scripts/SealSecret.sh
./scripts/SealSecret.sh <path to plain secret>
```

> ⚠️ If you are using Helm charts, make sure to place the sealed secret file under the directory ```your-app/templates```.

## Step 4: Add ArgoCD application
Now that the manifest files for your component are ready, the next step is to create the application for ArgoCD.

First, navigate to the ```application``` directory:

```sh
cd applications_sbx/release1
```

and create a folder with named as the namespace, or as your company, inside of it create a file named ```your-app.yaml``` with the following content:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: <app name>
  namespace: argocd
  labels:
    purpose: <app purpose>
spec:
  destination:
    namespace: <app namespace>
    server: https://kubernetes.default.svc
  project: default
  source:
    path: ionos_sbx/<app name>
    repoURL: https://github.com/DOME-Marketplace/dome-gitops
    targetRevision: HEAD
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

If your application is complex and consists of multiple components but you still want to manage it as a single ArgoCD application, you can use the following approach:

1. During the step [Add component manifest files](#step-3-add-component-manifest-files), create a directory for each sub-component (i.e. ```ionos_sbx/your-app/sub-component-1```, ```ionos_sbx/your-app/sub-component-2``` etc)
2. Create the directory ```applications_sbx/release1/your-app```
3. Inside ```applications_sbx/release1/your-app```, create an ArgoCD application file for each sub-component, ensuring that it points to the respective subfolder under ```ionos_sbx/your-app```

```yaml
source:
    path: ionos_sbx/<app name>/<sub-component name>
    repoURL: https://github.com/DOME-Marketplace/dome-gitops
    targetRevision: HEAD
```

4. Create an ArgoCD application file for your entire application and make it point to ```applications_sbx/release1/your-app```

```yaml
source:
    path: applications_sbx/release1/<app name>
    repoURL: https://github.com/DOME-Marketplace/dome-gitops
    targetRevision: HEAD
```

You can use the [marketplace](../applications_sbx/marketplace/bae-marketplace.yaml) application or for the contained approach [monitoring](../applications_sbx/monitoring.yaml) as a reference.

## Step 5: Create a Pull Request
Upon completing the changes, the team initiates a pull request from their branch to the main one. This PR serves as a formal request for the integration to be reviewed and merged. This PR must be named with the enviroment destination as prefix.   
Ex: **SBX - Deployment of myapp**  
Team members must wait for the review process to be completed. 

After an approval of the Merge Request be available to test as soon as possible the new deployed applicaiton.

> ⚠️ If someone else PR is merged before yours, your branch will result as Out Of Date. Please avoid to merge the main to our branch in order to update it. Instead make a **REBASE** of your branch following those step. 
>- ```git checkout main``` 
>- ```git fetch -p --all```
>- ```git pull```
>- ```git checkout <your_branch>```
>- ```git rebase main```
>- ```git status``` to ensure that you are still on your branch
>- ```git push --force```
>
> after that your branch and your Pull Request will be again Up-To-Date and mergeable. This approach ensure to maintain a readable git tree. 

Once the pull request is approved and merged into the main branch, the GitOps pipeline automatically triggers the deployment process. This involves synchronising the desired state of the cluster with the changes introduced in the merged pull request. The deployment is executed based on the Helm chart or manifest configurations added to the repository.
