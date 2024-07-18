Apply domains manually with commands:

    k apply -f domains_zammad-ingress.yaml
    k apply -f domains_argo-ingress.yaml
    k apply -f domains_bae-ingress.yaml
    k apply -f domains_verifier-ingress.yaml
    k apply -f domains_waltid-ingress.yaml
    k apply -f domains_chatbot-ingress.yaml
    k apply -f domains_cs-identity-ingress.yaml  - values.yaml need to be changed / app fix is necessary
    k apply -f domains_dome-wallet-keycloak-ingress.yaml -- not working, values.yaml need to be changed / app fix is necessary
    k apply -f domains_dome-wallet-ui-ingress.yaml -- not working, values.yaml need to be changed / app fix is necessary
    k apply -f domains_wallet-api-ingress.yaml -- working
    k apply -f domains_knowledgebase-ingress.yaml
    k apply -f domains_waltid-certs-ingress.yaml
 