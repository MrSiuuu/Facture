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

L’**interface** cycle de vie est en place : ajout de statut, historique, liste et détail des factures (stockage en mémoire).

### 1.2 Plan.md — couvert (sauf BDD et rapport)

| Élément plan | Statut |
|--------------|--------|
| Stack : Python, FastAPI, Jinja2, Uvicorn | ✅ |
| Architecture app / core / web (pas encore infra) | ✅ |
| 4.1 Upload facture (JSON ou XML) + lecture + objets + validations | ✅ |
| 4.2 Affichage : infos, vendeur, acheteur, lignes, totaux déclarés/recalculés, anomalies, décision | ✅ |
| 4.3 Cycle de vie : ajouter statut, voir historique, vérifier délais | ✅ (store + routes + templates) |
| 4.4 Liste des factures (déjà traitées) | ✅ (en mémoire) |
| 5.1–5.4 Modèles Party, InvoiceLine, Invoice, Lifecycle + méthodes | ✅ |
| 6. Services : Parser, Calculator (dans Invoice), Validator, Lifecycle checker + invoice_store | ✅ |
| 7. Base de données (infra, tables) | ❌ |
| 8. Routes : GET /, POST /process, GET /invoices, GET /invoices/{id}, POST /invoices/{id}/status | ✅ |

---

## 2. Ce qui reste à faire (ordre recommandé)

### Priorité 1 — Cycle de vie + liste/détail (sans BDD) — ✅ FAIT

1. ~~Stockage en mémoire~~ → `core/services/invoice_store.py` + enregistrement après POST /process.  
2. ~~GET /invoices~~ → `invoices_list.html`.  
3. ~~GET /invoices/{id}~~ → `invoice_detail.html` (détail + historique + is_open / is_paid / check_lifecycle).  
4. ~~POST /invoices/{id}/status~~ → formulaire + redirection vers le détail.  
5. ~~Premier statut RECEIVED~~ → ajouté automatiquement à la réception.

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

| # | Tâche | Statut |
|---|--------|--------|
| 1–5 | Stockage mémoire, GET /invoices, GET /invoices/{id}, POST …/status, affichage cycle de vie | ✅ Fait |
| 6 | Infra BDD : infra/db.py, repositories.py, tables | ❌ À faire |
| 7 | Brancher routes sur PostgreSQL/Supabase | ❌ À faire |
| 8 | Rapport écrit (métier, classes, règles, anomalies, cycle de vie) | ❌ À faire |
| 9 | Tests manuels complets | Optionnel |

---

## 4. Prochaine action recommandée

Pour **livrer le TP** : le cœur métier + l’interface (upload, liste, détail, cycle de vie) sont en place. Il reste au choix :
- **Option A** : rédiger le **rapport** (obligatoire pour le rendu) ; la BDD peut rester pour plus tard.
- **Option B** : ajouter l’**infra BDD** (plan §7) puis le rapport.
