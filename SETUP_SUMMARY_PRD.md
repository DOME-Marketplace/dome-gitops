
    k config use-context cluster-admin@DOME-Production-K8S
    create ns argocd
    kubectl apply -f applications_prd/namespaces.yaml -n argocd
    kubectl apply -k ./extension/ -n argocd
    kubectl apply -f applications/namespaces.yaml -n argocd
    kubectl apply -f applications/sealed-secrets.yaml -n argocd
    kubectl apply -f applications/ingress.yaml -n argocd

    # test ingress
    k create ns echoserver
    k apply -f ionos_prd/external-dns-ionos-webhook/test-ingress/echoserver_app_no_domain.yaml
    curl http://212.132.90.194/test

    # cert manager
    kubectl apply -f applications_prd/cert-manager.yaml -n argocd

    # ArgoCD
    - adapt /argocd/configmap.yaml (url, clientID)
    - adapt /argocd/ingress.yaml (cert-manager.io/cluster-issuer, host, hosts)
    - adapt /argocd/github-selaed-secret.yaml - generate secret based on GitHub secret
    kubectl apply -f applications_prd/argocd.yaml -n argocd
    # confirm that URL https://argocd.dome-marketplace-prd.org/ is available and SSL is working
    # Fix github-secret Sealed Secret
    
    # Generate and apply Sealed Secrets
    kubectl apply -f ionos_prd/marketplace/webhook/webhook-tls-sealed-secret.yaml

    



