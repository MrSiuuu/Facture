# Application de facturation électronique (PDP) — TP POO Python

Ce projet implémente une mini‑plateforme de dématérialisation partenaire (PDP) en Python.
L’objectif est de charger des factures Factur‑X au format JSON, de les modéliser avec des classes
Python, d’appliquer des contrôles métier/fiscaux et de suivre le cycle de vie de la facture.

## Prérequis

- Python 3.10+ recommandé
- `pip` installé

## Installation

```bash
pip install -r requirements.txt
```

## Lancer l’application

Depuis le dossier du projet :

```bash
uvicorn app.main:app --reload
```

Ensuite, ouvrir le navigateur sur : `http://localhost:8000`.

## État du projet

Le cœur métier se trouve dans le dossier `core` (modèles, services, validations).
La partie web (FastAPI + templates Jinja2) se trouve dans le dossier `app` / `web`.
La base de données et l’accès à PostgreSQL (Supabase) seront ajoutés dans `infra` plus tard.

