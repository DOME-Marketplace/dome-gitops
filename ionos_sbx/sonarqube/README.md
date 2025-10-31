
# SonarQube

This section explains how to install the Helm chart for SonarQube Server’s.

```bash
    helm repo add sonarqube https://SonarSource.github.io/helm-chart-sonarqube
    helm repo update
    kubectl create namespace sonarqube # If you dont have permissions to create the namespace, skip this step and replace all -n with an existing namespace name.
    helm upgrade --install -n sonarqube sonarqube sonarqube/sonarqube -f values.yaml
```