# Container Registry
## Introduction

Private Container Registry has been setup in order to enable own storage of Docker Images used in Dome project that are at risk to disappear from Docker image repositories currently in use.

Registry URL:
https://dcd.ionos.com/latest/#/registries/99a97546-73c3-4c29-92f2-a3c8b017ce51/repositories

## How registry was created:
- go to DCD
- Menu ‘Containers’
- Item ‘Container Registry’
- Click ‘Add a Registry’
- Registry name: “dome-registry”
- Wait until the status is ‘Running’


## Tokens
In order to access the registry 2 tokens have been created with 2 different roles:
- dome-pull: read only access (for application developers), with password referenced as $dockerPullPassword
- dome-push: read and write access (for DevOps team), with password referenced as $dockerPushPassword

## Access to registry / secrets
Each namespace that needs access to the registry has to configure access in the form of a secret.
Sample command to register a secret:

    kubectl create secret docker-registry ionos-regcred -n $namespaceName --docker-server=dome-registry.cr.de-fra.ionos.com --docker-username=dome-pull --docker-password=$dockerPullPassword

## Upload images to registry
Upload of images consists of the following steps:
- pull
- tag
- push

For example:

    docker login dome-registry.cr.de-fra.ionos.com -u dome-push -p $dockerPushPassword
    docker pull docker.io/bitnamilegacy/keycloak:24.0.4-debian-12-r1
    docker tag docker.io/bitnamilegacy/keycloak:24.0.4-debian-12-r1 dome-registry.cr.de-fra.ionos.com/keycloak:24.0.4-debian-12-r1
    docker push dome-registry.cr.de-fra.ionos.com/keycloak:24.0.4-debian-12-r1
    
So far all images with URL starting with docker.io/bitnamilegacy have been uploaded to the registry.

## Usage

In Deployment / Pod definition change image repository to ‘dome-registry.cr.de-fra.ionos.com’ and define imagePullSecrets.name property equal to ‘ionos-regcred’.
For example:

    imagePullSecrets:
        - name: ionos-regcred
    containers:
        - image: dome-registry.cr.de-fra.ionos.com/echo-server-dome:1.1
          imagePullPolicy: IfNotPresent
          name: echoserver

Please be aware that new registry requires authentication which is configured in ionos-regcred secret for each namespace.
Currently repository authentication has been defined for the following namespaces:
- cs-identity
- dome-certification
- in2
- knowledgebase
- marketplace
- sealed-secret
- zammad

If you have image in namespace not included in this list please submit a ticket to add secret to the specified namespace.

