
# Harbor

Harbor is an open source registry that secures artifacts with policies and role-based access control, ensures images are scanned and free from vulnerabilities, and signs images as trusted.

```bash
    helm repo add harbor https://helm.goharbor.io
    helm repo update
    kubectl create namespace harbor
    helm upgrade --install -n harbor harbor/harbor -f values.yaml
```