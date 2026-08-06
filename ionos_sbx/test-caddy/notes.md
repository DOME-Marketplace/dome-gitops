# test-caddy — validazione Caddy come load balancer / reverse proxy (SBX)

Namespace di test per valutare **Caddy Ingress Controller** in sostituzione di
`ingress-nginx`. Approvato per SBX da G. Cossu, sottodominio concordato con
Souvik: `tmf-test.dome-marketplace-sbx.org`.

Il test e' un **A/B a parita' di applicazione**: la stessa identica immagine
(`ealen/echo-server`) viene esposta due volte, una dal LoadBalancer di Caddy e
una da quello di nginx. echo-server risponde con il dump della richiesta, quindi
il confronto dei due output mostra subito cosa cambia nel percorso di rete
(`Host`, `X-Forwarded-For`, `X-Forwarded-Proto`, `X-Real-IP`, path riscritto,
terminazione TLS). Se un comportamento si vede su entrambi, non e' colpa di
Caddy.

## Cosa viene creato

| Risorsa | Path | Note |
|---|---|---|
| Caddy Ingress Controller | `ionos_sbx/caddy-ingress` | namespace `caddy-ingress`, chart `caddy-ingress-controller` 1.3.0, `Service` type `LoadBalancer` (IP pubblico **nuovo**, separato da nginx) |
| ClusterIssuer di test | `ionos_sbx/cert-manager/templates/caddy-test-issuer.yaml` | `letsencrypt-caddy-test-issuer`, solver HTTP01 su `ingressClassName: caddy`, ristretto al solo `tmf-test.dome-marketplace-sbx.org` |
| Pod #1 — via **Caddy** | `via-caddy-*.yaml` | `tmf-test.dome-marketplace-sbx.org` → LB Caddy → `echo-via-caddy:8080` |
| Pod #2 — via **nginx** | `via-nginx-*.yaml` | `tmf-test-nginx.dome-marketplace-sbx.org` → LB nginx → `echo-via-nginx:8080` |

I due pod sono identici in tutto (immagine, env, probe, resources): l'unica
differenza e' l'`ingressClassName` del rispettivo Ingress, e quindi il
LoadBalancer da cui entra il traffico.

## Isolamento rispetto agli altri team

- Il controller Caddy ha `classNameRequired: true` e `className: caddy`:
  **ignora** tutti gli Ingress esistenti, che non dichiarano quella class.
- `ingress-nginx` non viene modificato in alcun modo. Il pod #2 usa il
  controller nginx esistente esattamente come qualsiasi altro servizio.
- Il `ClusterIssuer` esistente `letsencrypt-sbx-issuer` non viene toccato: il
  nuovo issuer ha un `selector.dnsNames` limitato al solo host di Caddy.
- Nuovo LoadBalancer per Caddy, quindi nuovo IP: gli URL esistenti continuano a
  risolvere sull'IP di nginx.

## Passi manuali (in ordine)

0. **Push del branch.** Le due Application puntano a
   `targetRevision: test-caddy-integration`, e Argo legge da GitHub, non dal
   working copy: finche' il branch remoto non contiene questi file, le
   Application restano vuote.

       git push origin test-caddy-integration

1. Applicare le due Application. La CI gira solo su push a `main`, quindi
   durante il test vanno applicate a mano:

       kubectl apply -f applications_sbx/infrastructure/caddy-ingress.yaml -n argocd
       kubectl apply -f applications_sbx/test-caddy.yaml -n argocd

       # verifica che Argo abbia trovato i manifest sul branch giusto
       kubectl get application caddy-ingress test-caddy -n argocd

2. Recuperare i due IP pubblici:

       # IP NUOVO, dedicato a Caddy
       kubectl get svc caddy-ingress -n caddy-ingress -o wide
       # IP gia' esistente, quello di tutti gli altri host SBX
       kubectl get svc ingress-nginx-controller -n ingress-nginx -o wide

3. **Chiedere a Souvik due record DNS** (external-dns non e' attivo su SBX come
   Application Argo, quindi vanno creati lato IONOS DNS):

   | Host | Tipo | Target |
   |---|---|---|
   | `tmf-test.dome-marketplace-sbx.org` | `A` | IP del LB **Caddy** |
   | `tmf-test-nginx.dome-marketplace-sbx.org` | `A` | IP del LB **nginx** |

   Finche' il DNS non risolve, le challenge HTTP01 **falliscono** per entrambi.

4. Verificare l'emissione dei certificati:

       kubectl get certificate,certificaterequest,order,challenge -n test-caddy
       kubectl describe certificate echo-via-caddy-tls -n test-caddy
       kubectl describe certificate echo-via-nginx-tls -n test-caddy

5. Test end-to-end sui due percorsi:

       # entrambi devono rispondere 200 con il dump della richiesta
       curl -s https://tmf-test.dome-marketplace-sbx.org/       | jq . > /tmp/caddy.json
       curl -s https://tmf-test-nginx.dome-marketplace-sbx.org/ | jq . > /tmp/nginx.json

       # il confronto e' il vero risultato del test: cosa arriva all'upstream
       diff -u /tmp/nginx.json /tmp/caddy.json

       # catena TLS: deve essere Let's Encrypt, non il CA interno di Caddy
       for h in tmf-test tmf-test-nginx; do
         echo "== $h"
         echo | openssl s_client -connect $h.dome-marketplace-sbx.org:443 \
           -servername $h.dome-marketplace-sbx.org 2>/dev/null \
           | openssl x509 -noout -issuer -subject -dates
       done

       # redirect HTTP -> HTTPS su entrambi
       curl -sI http://tmf-test.dome-marketplace-sbx.org/
       curl -sI http://tmf-test-nginx.dome-marketplace-sbx.org/

6. Verificare che i due percorsi siano davvero separati: l'host di Caddy non
   deve rispondere sull'IP di nginx e viceversa (il traffico non deve
   "scavalcare" da un LB all'altro):

       curl -sI --resolve tmf-test.dome-marketplace-sbx.org:443:<IP_NGINX> \
         https://tmf-test.dome-marketplace-sbx.org/
       curl -sI --resolve tmf-test-nginx.dome-marketplace-sbx.org:443:<IP_CADDY> \
         https://tmf-test-nginx.dome-marketplace-sbx.org/

7. Log dei due controller (utili se una challenge non passa):

       kubectl logs -n caddy-ingress -l app.kubernetes.io/name=caddy-ingress-controller -f
       kubectl logs -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx -f

## Cose da tenere d'occhio

- **Rate limit Let's Encrypt**: per i primi giri conviene scommentare il
  server di staging in `caddy-test-issuer.yaml` (5 tentativi/ora per lo stesso
  set di host in produzione). Attenzione: il pod #2 usa
  `letsencrypt-sbx-issuer`, che e' **condiviso con tutta SBX** — non modificarlo
  per i test, e non ricreare in loop il suo Certificate.
- **Chicken-and-egg sulla challenge**: l'Ingress di Caddy dichiara `spec.tls`
  con un secret che all'inizio non esiste. cert-manager crea un Ingress
  temporaneo (class `caddy`) su `/.well-known/acme-challenge/...` servito in
  HTTP; se Caddy redirige a HTTPS, Let's Encrypt segue il redirect ignorando
  errori di certificato, quindi la validazione passa comunque. Se non passa, il
  punto da guardare e' se Caddy ha preso in carico l'Ingress di challenge
  (log del punto 7).
- **Nodo ingress tainted**: il controller Caddy ha `nodeSelector
  nodepool=ingress` + toleration `ingress-node=true:NoSchedule`, come nginx
  (cfr. `ionos_sbx/ingress/values.yaml`). Se i pod restano `Pending`, verificare
  label e taint del nodepool (`doc/devops/taints/TAINT_INGRESS_NODE.md`).
- **ACME nativo di Caddy disattivato** (`ingressController.config.email: ""`):
  i certificati arrivano solo da cert-manager. Se in futuro si volesse testare
  l'Automatic HTTPS di Caddy, basta valorizzare `email` e rimuovere
  l'annotation cert-manager dall'Ingress del pod #1.

## Prima del merge su main

Riportare `targetRevision` da `test-caddy-integration` a `HEAD` in **entrambe**
le Application:

- `applications_sbx/infrastructure/caddy-ingress.yaml`
- `applications_sbx/test-caddy.yaml`

Se il branch viene mergiato e poi cancellato senza questo passaggio, Argo resta
puntato a una revision che non esiste piu' e le due Application vanno in errore
di sync (`Unable to resolve revision`).

## Rollback

    kubectl delete -f applications_sbx/test-caddy.yaml -n argocd
    kubectl delete -f applications_sbx/infrastructure/caddy-ingress.yaml -n argocd
    kubectl delete namespace test-caddy caddy-ingress

Rimuovere poi i file dal repo (l'Application `infrastructure` ha `prune: true`,
quindi la cancellazione dei file basta a far rimuovere la child Application) e
chiedere a Souvik la rimozione dei due record DNS.
