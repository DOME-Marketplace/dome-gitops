# test-caddy — validazione Caddy come reverse proxy (SBX)

Namespace di test per valutare **Caddy Ingress Controller** in sostituzione di
`ingress-nginx`. Approvato per SBX da G. Cossu, sottodominio concordato con
Souvik: `tmf-test.dome-marketplace-sbx.org`.

## Cosa viene creato

| Risorsa | Path | Note |
|---|---|---|
| Caddy Ingress Controller | `ionos_sbx/caddy-ingress` | namespace `caddy-ingress`, chart `caddy-ingress-controller` 1.3.0, `Service` type `LoadBalancer` (IP pubblico **nuovo**, separato da nginx) |
| ClusterIssuer di test | `ionos_sbx/cert-manager/templates/caddy-test-issuer.yaml` | `letsencrypt-caddy-test-issuer`, solver HTTP01 su `ingressClassName: caddy`, ristretto al solo `tmf-test.dome-marketplace-sbx.org` |
| Pod #1 — con Ingress Caddy | `exposed-*.yaml` | `tmf-test.dome-marketplace-sbx.org` → `test-caddy-exposed-svc:8080` |
| Pod #2 — senza Ingress | `internal-*.yaml` | solo ClusterIP, controllo negativo |

Entrambi i pod usano `ealen/echo-server`, che risponde con il dump della
richiesta: si vede subito cosa Caddy inoltra all'upstream (`Host`,
`X-Forwarded-For`, `X-Forwarded-Proto`, path riscritto, ecc.).

## Isolamento rispetto agli altri team

- Il controller ha `classNameRequired: true` e `className: caddy`: **ignora**
  tutti gli Ingress esistenti, che non dichiarano quella class.
- `ingress-nginx` non viene modificato in alcun modo.
- Il `ClusterIssuer` esistente `letsencrypt-sbx-issuer` non viene toccato: il
  nuovo issuer ha un `selector.dnsNames` limitato al solo host di test.
- Nuovo LoadBalancer, quindi nuovo IP: gli URL esistenti continuano a
  risolvere sull'IP di nginx.

## Passi manuali (in ordine)

1. Sync delle Application (o merge su `main`, la CI applica tutto
   `applications_sbx/**`):

       kubectl apply -f applications_sbx/infrastructure/caddy-ingress.yaml -n argocd
       kubectl apply -f applications_sbx/test-caddy.yaml -n argocd

2. Recuperare l'IP pubblico del LoadBalancer di Caddy:

       kubectl get svc caddy-ingress -n caddy-ingress -o wide

3. **Chiedere a Souvik il record DNS** `tmf-test.dome-marketplace-sbx.org`
   → `A` → IP del punto 2. (external-dns non e' attivo su SBX come
   Application Argo, quindi il record va creato lato IONOS DNS.)
   Finche' il DNS non risolve su quell'IP, la challenge HTTP01 **fallisce**.

4. Verificare l'emissione del certificato:

       kubectl get certificate,certificaterequest,order,challenge -n test-caddy
       kubectl describe certificate test-caddy-tls-secret -n test-caddy

5. Test end-to-end:

       # deve rispondere 200 con il dump della richiesta
       curl -sv https://tmf-test.dome-marketplace-sbx.org/ | jq .

       # catena TLS: deve essere Let's Encrypt, non il CA interno di Caddy
       echo | openssl s_client -connect tmf-test.dome-marketplace-sbx.org:443 \
         -servername tmf-test.dome-marketplace-sbx.org 2>/dev/null \
         | openssl x509 -noout -issuer -subject -dates

       # redirect HTTP -> HTTPS
       curl -sI http://tmf-test.dome-marketplace-sbx.org/

6. Controllo negativo — il pod #2 non deve essere raggiungibile da fuori,
   solo dal cluster:

       kubectl exec -n test-caddy deploy/test-caddy-exposed-deployment -- \
         wget -qO- http://test-caddy-internal-svc:8080/

7. Log del controller (utile se la challenge non passa):

       kubectl logs -n caddy-ingress -l app.kubernetes.io/name=caddy-ingress-controller -f

## Cose da tenere d'occhio

- **Rate limit Let's Encrypt**: per i primi giri conviene scommentare il
  server di staging in `caddy-test-issuer.yaml` (5 tentativi/ora per lo stesso
  set di host in produzione).
- **Chicken-and-egg sulla challenge**: l'Ingress principale dichiara `spec.tls`
  con un secret che all'inizio non esiste. cert-manager crea un Ingress
  temporaneo (class `caddy`) su `/.well-known/acme-challenge/...` servito in
  HTTP; se Caddy redirige a HTTPS, Let's Encrypt segue il redirect ignorando
  errori di certificato, quindi la validazione passa comunque. Se non passa, il
  punto da guardare e' se Caddy ha preso in carico l'Ingress di challenge
  (log del punto 7).
- **Nodo ingress tainted**: il controller ha `nodeSelector nodepool=ingress` +
  toleration `ingress-node=true:NoSchedule`, come nginx. Se i pod restano
  `Pending`, verificare label e taint del nodepool
  (`doc/devops/taints/TAINT_INGRESS_NODE.md`).
- **ACME nativo di Caddy disattivato** (`ingressController.config.email: ""`):
  i certificati arrivano solo da cert-manager. Se in futuro si volesse testare
  l'Automatic HTTPS di Caddy, basta valorizzare `email` e rimuovere
  l'annotation cert-manager dall'Ingress.

## Rollback

    kubectl delete -f applications_sbx/test-caddy.yaml -n argocd
    kubectl delete -f applications_sbx/infrastructure/caddy-ingress.yaml -n argocd
    kubectl delete namespace test-caddy caddy-ingress

Rimuovere poi i file dal repo (l'Application `infrastructure` ha `prune: true`,
quindi la cancellazione dei file basta a far rimuovere la child Application).
