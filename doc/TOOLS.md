Tools used on the project: 

## Infrastructure
- [Ionos DCD](https://cloud.ionos.com/data-centers) - DataCenter Designer tool for infrastructure management 
- [ionosctl](https://docs.ionos.com/cli-ionosctl) - a tool that helps manage Ionos Cloud resources directly from terminal; used to define Data Center, Kubernetes Cluster and Node Pool
- [Ionos Cloud Managed Kubernetes Services](https://cloud.ionos.com/managed/kubernetes) - Kubernetes service provided by ION
- [ArgoCD](https://argo-cd.readthedocs.io/en/stable/ ) - a declarative, GitOps continuous delivery tool for Kubernetes
- [Sealed Secrets](https://github.com/bitnami-labs/sealed-secrets#kubeseal) - tool for sealing secrets using asymmetric cryptography; Using GitOps, means every deployed resource is represented in a git-repository. While this is not a problem for most resources, secrets need to be handled differently. We use the bitnami/sealed-secrets project for that. It uses asymmetric cryptography for creating secrets and only decrypt them inside the cluster. The sealed-secrets controller will be the first application deployed using ArgoCD
- [Ingress controller](https://kubernetes.io/docs/concepts/services-networking/ingress-controllers/) - necessary tool for an Ingress to work in your cluster. Ingress enables to access applications inside the cluster from the outside via subdomains, i.e. ticketing.dome-marketplace.eu
- [External DNS Ionos webhook](https://github.com/ionos-cloud/external-dns-ionos-webhook) makes it possible to automatically create DNS entries for [Ingress-Resources](https://kubernetes.io/docs/concepts/services-networking/ingress/). External-DNS watches the ingress objects and creates A-Records for them.
- [Cert Manager](https://cert-manager.io/) - used for automation of creation and update of valid certificates for new dns-entries of ingress resources. The certificates will be provided by [Lets encrypt](https://letsencrypt.org/).
- [Helm](https://helm.sh/) - package manager for Kubernetes in order to find, share and use software built for Kubernetes


## DevOps tools
- [kubectl](https://kubernetes.io/docs/reference/kubectl/) - command line tool for communicating with a Kubernetes cluster's control plane, using the Kubernetes API.
- [kubeseal](https://github.com/bitnami-labs/sealed-secrets#kubeseal) - command line tool for sealing secrets using asymmetric cryptography
- [k9s](https://k9scli.io/) - terminal based UI to interact with your Kubernetes clusters

## Monitoring and logging

- [Grafana Loki](https://grafana.com/oss/loki/) - Loki is a horizontally scalable, highly available, multi-tenant log aggregation system inspired by Prometheus. It is designed to be very cost effective and easy to operate. It does not index the contents of the logs, but rather a set of labels for each log stream.
- [Promtail Agent](https://grafana.com/docs/loki/latest/send-data/promtail/) - an agent which ships the contents of local logs to a private Grafana Loki instance or Grafana Cloud. It is usually deployed to every machine that runs applications which need to be monitored.
- [Grafana](https://grafana.com/) - multi-platform open source analytics and interactive visualization web application. It can produce charts, graphs, and alerts for the web when connected to supported data sources.
- [Prometheus](https://prometheus.io/) - an open-source systems monitoring and alerting toolkit
- [Falco](https://falco.org/) - a cloud native security tool that provides runtime security across hosts, containers, Kubernetes, and cloud environments

## Internally build tools
- Script for generating kube-config.yaml files for application owners to access environments with restricted rights to generate Sealed Secrets resources and manage them

