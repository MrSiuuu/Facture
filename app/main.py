import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from web.routes import router as web_router

# Clé secrète pour signer les cookies de session (à définir en prod via .env)
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me-in-production")

app = FastAPI(title="PDP Facturation électronique")

# Session : cookie signé, pas de BDD (déconnexion = tout perdu pour l'utilisateur)
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Routes (accueil, login, logout, upload, factures) — voir web/routes.py
app.include_router(web_router)

app.mount("/static", StaticFiles(directory="web/static"), name="static")

