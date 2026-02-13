# Kubeconfig Generator for Namespaces

This tool automates the creation of a restricted `kubeconfig` file for a specific Kubernetes Namespace.
It handles the creation of the Namespace, ServiceAccount, RBAC Roles, and generates the final configuration file used for authentication.

## Prerequisites

* **Linux/MacOS** environment (Bash shell).
* **kubectl** installed and configured with Admin rights to the cluster.
* **base64** utility installed.

## Setup

1.  Ensure the script has execution permissions:
    ```bash
    chmod +x generate_kubeconfig.sh
    ```
2.  Ensure your directory structure looks like this:
    ```text
    /
    ├── generate_kubeconfig.sh
    └── templates/
        ├── 00-namespace.yaml
        ├── ... (other manifests)
        └── config/
            └── kube-config-template.yaml
    ```

## Usage

Run the script with the following arguments:

```bash
./generate_kubeconfig.sh <TEMPLATE_PATH> <OUTPUT_PATH> <NAMESPACE> <ENV_SUFFIX>