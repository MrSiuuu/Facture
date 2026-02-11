# Plan d’implémentation — PDP Facturation électronique

Ce document décrit **ce qui est déjà fait** et **ce qui reste à faire**, en cohérence avec l’**énoncé du prof** (PDF) et ton **plan.md**.

---

## 1. Déjà implémenté (énoncé + plan)

### 1.1 Énoncé PDF — couvert

| Demande énoncé | Statut | Où c’est fait |
|----------------|--------|----------------|
| §3 Chargement / exploration (dict, numéro, date, devise, vendeur, acheteur, nb lignes) | ✅ | XML/JSON → dict (facturx_xml, parser) puis objets |
| §4 Classe Party (vendeur/acheteur) | ✅ | `core/models/party.py` |
| §5 Classe InvoiceLine + liste de lignes | ✅ | `core/models/invoice_line.py` |
| §6 Classe Invoice + résumé lisible | ✅ | `core/models/invoice.py` + `summary()` |
| §7 Calculs HT, TVA par taux, TTC + comparaison aux déclarés | ✅ | Méthodes sur `Invoice` + `validator.py` |
| §8 TVA, exonérations, TVA 0% → motif obligatoire | ✅ | `validator.py` (validate_vat_and_exemptions) |
| §9 Bonus : moteur validation (règles, erreurs, décision) | ✅ | `validator.py` (validate_invoice) |
| §10 Cycle de vie : statut/date/message, historique, délais, `is_open()`, `is_paid()`, `check_lifecycle()` | ✅ Cœur métier | `core/models/lifecycle.py` |

**Manque côté énoncé :** pas encore d’**interface** pour « ajouter un statut », « voir l’historique » ni pour « liste / détail des factures » (énoncé + plan.md).

### 1.2 Plan.md — couvert partiellement

| Élément plan | Statut |
|--------------|--------|
| Stack : Python, FastAPI, Jinja2, Uvicorn | ✅ |
| Architecture app / core / web (pas encore infra) | ✅ |
| 4.1 Upload facture (JSON ou XML) + lecture + objets + validations | ✅ |
| 4.2 Affichage : infos, vendeur, acheteur, lignes, totaux déclarés/recalculés, anomalies, décision | ✅ |
| 4.3 Cycle de vie : **ajouter statut, voir historique, vérifier délais** | ❌ Pas encore dans l’interface |
| 4.4 Liste des factures (déjà traitées) | ❌ Pas encore |
| 5.1–5.4 Modèles Party, InvoiceLine, Invoice, Lifecycle + méthodes | ✅ |
| 6. Services : Parser, Calculator (dans Invoice), Validator, Lifecycle checker | ✅ |
| 7. Base de données (infra, tables) | ❌ |
| 8. Routes : GET /, POST /process | ✅ |
| 8. Routes : GET /invoices, GET /invoices/{id}, POST /invoices/{id}/status | ❌ |

---

## 2. Ce qui reste à faire (ordre recommandé)

### Priorité 1 — Cycle de vie + liste/détail (sans BDD)

1. **Stockage en mémoire des factures traitées**  
   - Après `POST /process`, enregistrer l’`Invoice` dans un dict global (ou par session) : `id → Invoice`.  
   - Permet de délivrer tout de suite les routes suivantes.

2. **GET /invoices**  
   - Afficher la liste des factures traitées (numéro, date, vendeur, acheteur, décision, statut actuel).  
   - Template `invoices_list.html`.

3. **GET /invoices/{id}**  
   - Page détail d’une facture : même contenu que la page résultat actuelle + **historique des statuts** + résultat de `check_lifecycle()` + indicateurs `is_open()` / `is_paid()`.  
   - Template `invoice_detail.html` (ou réutiliser `result_invoice.html` avec bloc « cycle de vie »).

4. **POST /invoices/{id}/status**  
   - Formulaire ou appel pour **ajouter un changement de statut** (RECEIVED, VALIDATED, MISE_EN_PAIEMENT, PAYEE, REJECTED) avec message optionnel.  
   - Appeler `invoice.lifecycle.add_status(statut, date, message)`, puis réafficher le détail (ou rediriger vers GET /invoices/{id}).

5. **Premier statut à la réception**  
   - Lors du `POST /process`, ajouter automatiquement un statut initial (ex. RECEIVED) avec la date courante pour que le cycle de vie soit visible tout de suite.

### Priorité 2 — Base de données (plan.md §7 + §8)

6. **Créer `infra/`**  
   - `db.py` : connexion PostgreSQL avec `DATABASE_URL` (`.env`).  
   - `repositories.py` : sauvegarde / chargement factures, lignes, historique de statuts (tables `invoices`, `invoice_lines`, `status_history`).

7. **Brancher les routes sur la BDD**  
   - POST /process → enregistrer la facture en base après validation.  
   - GET /invoices → lire depuis la BDD.  
   - GET /invoices/{id} → charger depuis la BDD.  
   - POST /invoices/{id}/status → enregistrer le nouveau statut en base + mettre à jour l’objet.

### Priorité 3 — Finition

8. **Tests manuels**  
   - Upload XML, vérifier calculs, validation, puis liste, détail, ajout de statuts, vérification des délais.

9. **Rapport (doc)**  
   - Compréhension métier, justification des classes, règles implémentées, anomalies, cycle de vie (comme prévu dans l’énoncé et plan.md §11).

---

## 3. Récap : ce qui reste (liste courte)

| # | Tâche | Réf. énoncé / plan |
|---|--------|---------------------|
| 1 | Stockage en mémoire des factures après POST /process | plan §4.4, §8 |
| 2 | GET /invoices (liste) | plan §4.4, §8 |
| 3 | GET /invoices/{id} (détail + cycle de vie) | plan §4.2, §4.3, §8 |
| 4 | POST /invoices/{id}/status (ajout statut) | plan §4.3, §8 |
| 5 | Afficher historique des statuts + is_open / is_paid / check_lifecycle dans l’UI | énoncé §10, plan §4.3 |
| 6 | Infra BDD : infra/db.py, repositories.py, tables | plan §7 |
| 7 | Brancher routes sur PostgreSQL/Supabase | plan §7, §8 |
| 8 | Rapport écrit | énoncé consignes, plan §11 |

---

## 4. Prochaine action recommandée

Enchaîner sur **Priorité 1** : stockage en mémoire + GET /invoices + GET /invoices/{id} + POST /invoices/{id}/status + affichage du cycle de vie dans les templates. Ensuite seulement BDD + rapport.
