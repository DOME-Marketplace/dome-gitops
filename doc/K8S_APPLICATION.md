# Create K8s manifest files for your application

This guide explains how to create the manifest files necessary to deploy your application on a Kubernetes cluster. 

For demonstration purposes, we will use a sample docker-compose file descibing a simple application with a MySql database and convert its services into proper manifest files.

``` yaml
version: '3'
services:

  mysql:
    image: mysql:8.2
    ports:
      - "3406:3306"
    environment:
      MYSQL_ROOT_PASSWORD: secret
      MYSQL_DATABASE: my-app-db
      MYSQL_USER: username
      MYSQL_PASSWORD: secret
    volumes:
      - 'mysql-data:/var/lib/mysql'
  
  my-app:
    image: registry/my-app:1.0.0
    ports:
      - "8080:8080"
    environment:
      SERVER_PORT: 8080
      DB_HOST: mysql:3306
      DB_DATABASE: bookstack
      DB_USERNAME: my-app-db
      DB_PASSWORD: secret
    volumes:
      - 'app-data:/home/app/data'

volumes:
  mysql-data:
  app-data:
```

## Use available Helm Charts whenever possibile

If your application relies on database or other third-party software, you should use their corresponding Helm charts. In this repository, you can find several examples of using Helm charts to deploy databases and other tools. Here are some examples:

- [MySql](../ionos/dome-trust/mysql/Chart.yaml)
- [MongoDb](../ionos/marketplace/mongodb/Chart.yaml)
- [Kafka](../ionos/marketplace/kafka/Chart.yaml)

> Remember to add required secrets within the ```templates``` folder

## Manifest files

> ⚠️ The resources described below are those required for deploying the sample application. Other applications may require additional resources or may not need all those described.

### Deployment

A [Deployment](https://kubernetes.io/docs/concepts/workloads/controllers/deployment) provides declarative updates for Pods and ReplicaSets. You describe a desired state in a Deployment, and the Deployment Controller changes the actual state to the desired state.

Here is the deployment file for the demo application:

``` yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
  namespace: my-app
  labels:
    app.kubernetes.io/instance: my-app
    app.kubernetes.io/name: my-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app.kubernetes.io/instance: my-app
      app.kubernetes.io/name: my-app
  template:
    metadata:
      labels:
        app.kubernetes.io/instance: my-app
        app.kubernetes.io/name: my-app
    spec:
      containers:
        - name: my-app
          image: registry/my-app:1.0.0
          env:
            - name: SERVER_PORT
              value: 8080
            - name: DB_HOST
              value: "<name of mysql service>:3306"
            - name: DB_DATABASE
              value: my-app-db
            - name: DB_USERNAME
              value: username
            - name: DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: my-app-secret
                  key: DB_PASSWORD
          ports:
            - containerPort: 8080
              name: http
              protocol: TCP
          volumeMounts:
            - mountPath: /home/app/data
              name: my-app-storage
      volumes: 
      - name: my-app-storage
        persistentVolumeClaim:
          claimName: my-app-pvc
```

**Notes**
- The name of MySql service should be set in the corresponding Helm Chart within the values file
- The value of ```claimname``` must match the one used in the Persistent Volume Claim file.

### Persistent Volume Claim

A PersistentVolumeClaim (PVC) is a request for [storage](https://kubernetes.io/docs/concepts/storage) by a user. Claims can request specific size and access modes.

Here is the PVC file for the demo application:

``` yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: my-app-pvc
  namespace: my-app
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
```

### Service

A [Service](https://kubernetes.io/docs/concepts/services-networking/service) is a method for exposing a network application that is running as one or more Pods in your cluster.

Here is the service file for the demo application:

``` yaml
apiVersion: v1
kind: Service
metadata:
  name: my-app
  namespace: my-app
spec:
  type: ClusterIP
  selector:
    app.kubernetes.io/instance: my-app
    app.kubernetes.io/name: my-app
  ports:
    - name: http
      port: 8080
      protocol: TCP
      targetPort: 8080
```

### Ingress

A [Ingress](https://kubernetes.io/docs/concepts/services-networking/ingress) is an API object that manages external access to the services in a cluster, typically HTTP. Ingress may provide load balancing, SSL termination and name-based virtual hosting.

Here is the ingress file for the demo application:

``` yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-app-ingress
  namespace: my-app
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-dev-issuer
    nginx.ingress.kubernetes.io/ssl-passthrough: "true"
    nginx.ingress.kubernetes.io/backend-protocol: "HTTP"
spec:
  ingressClassName: nginx
  rules:
  - host: my-app.dome-marketplace-dev.org
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: my-app
            port:
              number: 8080
  tls:
  - hosts:
    - my-app.dome-marketplace-dev.org
    secretName: my-app-tls-secret
```

**Notes**
- Hosts are automatically craeted and managed by External-DNS
- The value of ```backend.service.name``` must match the name of the [Service](#service)
- The value of ```backend.service.port.number``` must match the one defined in the [Service](#service)

### Secret

A [Secret](https://kubernetes.io/docs/concepts/configuration/secret) is an object that contains a small amount of sensitive data such as a password, a token, or a key. Using a Secret means that you don't need to include confidential data in your application code.

Here is the secret file for the demo application:

``` yaml
apiVersion: v1
kind: Secret
metadata:
  name: my-app-secret
  namespace: my-app
stringData:
  DB_PASSWORD: "secret"
```

> ⚠️ Remember, plain secrets should never be pushed to the repository. You should first encrypt them using SealedSecret as described [here](./INTEGRATION.md/#add-secrets).