# Cahier des charges — Application PDP de facturation électronique
TP POO Python
## 1. Objectif du projet
Développer une application simulant une Plateforme de Dématérialisation Partenaire (PDP).

L’application doit permettre de :
- charger une facture électronique au format JSON,
- modéliser cette facture en objets Python,
- appliquer des contrôles métier et fiscaux,
- recalculer les montants,
- décider si la facture est valide ou rejetée,
- suivre le cycle de vie via des statuts horodatés,
- afficher les résultats dans une interface web.

Le développement doit respecter une architecture orientée objet claire.
Le cœur métier doit être totalement indépendant de l’interface.

Le rapport sera rédigé après le développement à partir des éléments implémentés.
## 2. Stack technique imposée
Backend :
- Python
- FastAPI
Frontend :
- Jinja2 (templates HTML)
- Bootstrap ou CSS simple
Base de données :
- PostgreSQL (hébergé sur Supabase)
Serveur :
- Uvicorn
Configuration :
- variables d’environnement via `.env`
## 3. Architecture globale

Principe fondamental :
la logique demandée dans le TP doit vivre dans le dossier `core`.
La partie web ne fait qu’appeler cette logique.
app/  
main.py

core/  
models/  
services/

web/  
routes.py  
templates/

infra/  
db.py  
repositories.py
## 4. Fonctionnalités applicatives à livrer

### 4.1 Upload d’une facture
L’utilisateur peut charger un fichier JSON.

Le système doit :
- lire le fichier,
- transformer les données en objets métier,
- exécuter validations et calculs.
### 4.2 Affichage d’une facture
La page résultat doit montrer :
- informations générales,
- vendeur,
- acheteur,
- lignes de facture,
- totaux déclarés,
- totaux recalculés,
- anomalies détectées,
- décision finale (VALIDATED / REJECTED).
### 4.3 Cycle de vie
L’application doit permettre :
- d’ajouter des changements de statut,
- de voir l’historique,
- de vérifier automatiquement les délais réglementaires.

Statuts possibles :
RECEIVED → VALIDATED → MISE_EN_PAIEMENT → PAYEE  
ou REJECTED.
### 4.4 Liste des factures
Une page doit permettre de consulter les factures déjà traitées si elles sont enregistrées en base.
## 5. Modélisation objet (COEUR DU TP)

### 5.1 Party
Représente vendeur ou acheteur.

Attributs :
- identifiant
- nom
- adresse
- pays
- identifiants fiscaux
### 5.2 InvoiceLine
Attributs :
- id ligne
- description
- quantité
- prix unitaire
- montant HT
- taux TVA
- catégorie TVA
- motif exonération
### 5.3 Invoice
Regroupe :
- informations générales
- seller
- buyer
- liste de lignes
- montants déclarés
- anomalies
- décision

Méthodes importantes :
- summary()
- compute_totals()
### 5.4 Lifecycle
Modélise :
- statut
- date
- message

Gestion :
- historique des changements
- respect des délais

Méthodes obligatoires :
- is_open()
- is_paid()
- check_lifecycle()

## 6. Services métier

### Parser
Transforme le JSON en objets.

### Calculator
Recalcule :
- total HT
- TVA par taux
- total TTC

### Validator
Vérifie :
- cohérence montants calculés vs déclarés,
- cohérence TVA,
- TVA à 0% → motif obligatoire.

Produit :
- liste d’erreurs
- décision VALIDATED ou REJECTED.

### Lifecycle checker
Contrôle les dépassements de délais.
## 7. Base de données

Objectif :
permettre de conserver les factures et leur historique.

Tables minimales :
- invoices
- invoice_lines
- status_history

Connexion via :
DATABASE_URL dans les variables d’environnement.
## 8. Routes web attendues

GET /
→ page upload

POST /process
→ parsing + validation + affichage résultat

GET /invoices
→ liste

GET /invoices/{id}
→ détail

POST /invoices/{id}/status
→ ajout statut
## 9. Contraintes de développement

- typage Python recommandé
- séparation stricte métier / web
- code lisible
- méthodes claires
- erreurs explicites
- aucune règle métier dans les templates
## 10. Ordre d’implémentation

### Étape 1
Structure du projet + FastAPI opérationnel.
### Étape 2
Exploration JSON sans classes.
### Étape 3
Implémentation des modèles :
Party, InvoiceLine, Invoice.
### Étape 4
Parser JSON → objets.
### Étape 5
Calculs financiers.
### Étape 6
Moteur de validation.
### Étape 7
Cycle de vie + délais.
### Étape 8
Interface web.
### Étape 9
Connexion Supabase.
### Étape 10
Tests complets via l’interface.

## 11. Rapport (à produire après développement)

Le rapport devra expliquer :
- compréhension métier,
- justification des classes,
- règles implémentées,
- gestion des anomalies,
- fonctionnement du cycle de vie.

Il s’appuiera sur l’architecture réellement développée.

