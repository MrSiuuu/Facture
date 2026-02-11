from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request

from web.routes import router as web_router


app = FastAPI(title="PDP Facturation électronique")

# Templates Jinja2 (pour les vues HTML)
templates = Jinja2Templates(directory="web/templates")


@app.get("/", name="home")
async def home(request: Request):
    """
    Page d'accueil minimale avec lien vers le formulaire d'upload.
    """
    return templates.TemplateResponse("index.html", {"request": request})


# Inclusion des autres routes applicatives
app.include_router(web_router)


# Optionnel : servir des fichiers statiques plus tard (CSS, JS…)
app.mount("/static", StaticFiles(directory="web/static"), name="static")

