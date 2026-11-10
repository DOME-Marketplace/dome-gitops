# Containers Images Extractor

`images-extractor.py` lists the container images running in each DOME environment
(`sbx`, `dev`, `dev2`, `prd`). It queries the environments live with `kubectl`, so it
reports what is actually deployed, which may differ from this repo.

For each environment it collects every container of every pod in all namespaces
and records:

- namespace, pod, service and container name
- the image and tag declared in the pod spec, and the image reported by the running container
- a warning when the tag is missing (`NO TAG`) or is `latest` (`LATEST`)

It then writes:

- **`<env>.csv`**: one file per environment with the raw data.
- **`images.xlsx`**: one sheet per environment, with two extra columns:
  - **application**: the ArgoCD Application that manages the pod. Pods from a
    Helm release that ArgoCD does not manage are marked `[manual]` and
    highlighted in yellow.
  - **company**: the partner responsible for the component, looked up in
    [`components-partner.csv`](components-partner.csv).

Output goes to a new timestamped directory, e.g. `output/2026.10.02_17.08.00/`.
The `output/` directory is git-ignored.

## Requirements

- Python 3.9+ with `openpyxl` (`pip install openpyxl`)
- `kubectl`
- One kubeconfig per environment, with permission to list pods in all
  namespaces. Reading ArgoCD Applications in the `argocd` namespace is optional:
  if they cannot be read, every pod deployed with Helm is shown as `[manual]`.

> **Kubeconfig files contain cluster credentials. Keep them outside this repository.**

## Usage

By default the script looks for the kubeconfig files here:

```text
~/.kube/dome/sbx/kubeconfig.yaml
~/.kube/dome/dev/kubeconfig.yaml
~/.kube/dome/dev2/kubeconfig.yaml
~/.kube/dome/prd/kubeconfig.yaml
```

If your files are there, run it without arguments, from any directory:

```bash
python3 scripts/containers-images-extractor/images-extractor.py
```

If your kubeconfig files are somewhere else, pass a path template where `{env}`
is replaced with each environment name. You can pass it in either of two ways:

```bash
# 1. command-line option
python3 images-extractor.py --kubeconfig-template /path/to/kubeconfigs/{env}/kubeconfig.yaml

# 2. environment variable, e.g. in ~/.bashrc
export KUBECONFIG_TEMPLATE=/path/to/kubeconfigs/{env}/kubeconfig.yaml
python3 images-extractor.py
```

The template can contain `~` and environment variables. If more than one is set,
the command-line option wins over `KUBECONFIG_TEMPLATE`, which wins over the
default. At startup the script prints which template it is using and where the
template came from.

### Options

| Option | Default | Description |
|---|---|---|
| `--kubeconfig-template TEMPLATE` | `$KUBECONFIG_TEMPLATE`, then `~/.kube/dome/{env}/kubeconfig.yaml` | Path of the kubeconfig files, with `{env}` as placeholder |
| `--output-dir DIR` | `output/` next to the script | Where the timestamped report directory is created |
| `--partners-csv FILE` | `components-partner.csv` next to the script | Namespace/component → partner mapping |

Run `python3 images-extractor.py --help` for the full help.

### Missing environments

- If an environment's kubeconfig file does not exist, the script prints a
  `SKIPPED` warning and goes on with the other environments.
- If `kubectl` fails for an environment, the script prints the error and goes on
  with the other environments.
- If no kubeconfig file is found at all, the script stops. It lists the paths it
  looked up and explains how to point it to the right ones.

## Partners mapping

`components-partner.csv` has the columns `Namespace, Partner, Component`.
To find the partner, the script tries, in this order:

1. exact match on namespace and component
2. namespace only, when only one partner owns that namespace
3. exact match on component, in any namespace
4. fuzzy match on component

Some Kubernetes namespaces have a different name in the CSV, for example
`zammad` → `customer service`. These aliases are defined in `NS_ALIASES` in the
script. When a pod gets no partner or the wrong one, add a row to the CSV or
add an alias.
