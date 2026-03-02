import json
import os
import uuid
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from core.models.lifecycle import InvoiceStatus
from core.services.parser import parse_invoice_from_json
from core.services.facturx_xml import facturx_xml_to_dict
from core.services.validator import validate_invoice
from core.services.invoice_store import (
    add as store_add,
    get as store_get,
    list_all as store_list_all,
    clear_session as store_clear_session,
)

# Identifiants de connexion (sans BDD) — configurables via .env
LOGIN_USERNAME = os.getenv("LOGIN_USERNAME", "demo")
LOGIN_PASSWORD = os.getenv("LOGIN_PASSWORD", "demo")

router = APIRouter()
templates = Jinja2Templates(directory="web/templates")


def _require_auth(request: Request) -> str | RedirectResponse:
    """
    Retourne le session_id si l'utilisateur est connecté,
    sinon une RedirectResponse vers /login.
    """
    if not request.session.get("user"):
        return RedirectResponse(url="/login", status_code=302)
    session_id = request.session.get("session_id")
    if not session_id:
        return RedirectResponse(url="/login", status_code=302)
    return session_id


# ---------- Login / Logout (sans BDD) ----------


@router.get("/login", response_class=HTMLResponse, name="login")
async def login_page(request: Request):
    """Affiche le formulaire de connexion."""
    if request.session.get("user"):
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": None},
    )


@router.post("/login", name="login_submit")
async def login_submit(
    request: Request,
    username: str = Form(..., alias="username"),
    password: str = Form(..., alias="password"),
):
    """Vérifie les identifiants et crée la session (cookie signé)."""
    if request.session.get("user"):
        return RedirectResponse(url="/", status_code=302)

    if username != LOGIN_USERNAME or password != LOGIN_PASSWORD:
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": "Identifiant ou mot de passe incorrect.",
            },
            status_code=401,
        )

    request.session["user"] = username
    request.session["session_id"] = str(uuid.uuid4())
    return RedirectResponse(url="/", status_code=302)


@router.get("/logout", name="logout")
async def logout_page(request: Request):
    """Déconnexion : suppression des factures de la session + vidage du cookie."""
    session_id = request.session.get("session_id")
    if session_id:
        store_clear_session(session_id)
    request.session.clear()
    return RedirectResponse(url="/login", status_code=302)


# ---------- Routes protégées (accueil, upload, factures) ----------


@router.get("/", response_class=HTMLResponse, name="home")
async def home(request: Request):
    """Page d'accueil (après connexion)."""
    auth = _require_auth(request)
    if isinstance(auth, RedirectResponse):
        return auth
    return templates.TemplateResponse("index.html", {"request": request})


def _load_invoice_data(raw_content: str, filename: str | None) -> tuple[dict | None, str | None]:
    """
    Charge les données de facture depuis le contenu brut.
    - Si le fichier est en .xml : parse XML Factur-X → dict normalisé.
    - Sinon : parse JSON → dict.
    Retourne (data, error). Si error n'est pas None, data peut être None.
    """
    is_xml = filename and filename.lower().endswith(".xml")
    if is_xml:
        try:
            data = facturx_xml_to_dict(raw_content)
            return data, None
        except Exception as exc:
            return None, f"Erreur lecture XML Factur-X : {exc}"
    try:
        data = json.loads(raw_content)
        return data, None
    except json.JSONDecodeError as exc:
        return None, f"JSON invalide : {exc}"


@router.get("/upload", response_class=HTMLResponse, name="upload_invoice")
async def upload_page(request: Request):
    """Formulaire d'upload de facture (JSON ou XML Factur-X)."""
    auth = _require_auth(request)
    if isinstance(auth, RedirectResponse):
        return auth
    return templates.TemplateResponse("upload.html", {"request": request})


@router.post("/process", response_class=HTMLResponse, name="process_invoice")
async def process_invoice(
    request: Request,
    file: UploadFile = File(..., description="Fichier JSON ou XML Factur-X"),
):
    """Traite le fichier uploadé et enregistre la facture dans la session."""
    auth = _require_auth(request)
    if isinstance(auth, RedirectResponse):
        return auth
    session_id = auth

    content_bytes = await file.read()
    raw_content = content_bytes.decode("utf-8", errors="replace")

    data, load_error = _load_invoice_data(raw_content, file.filename)
    if load_error is not None:
        return templates.TemplateResponse(
            "result_raw.html",
            {
                "request": request,
                "filename": file.filename,
                "raw_content": raw_content,
                "error": load_error,
            },
        )

    invoice = parse_invoice_from_json(data)
    decision, anomalies = validate_invoice(invoice)

    # Premier statut : réception (conformément au cycle de vie PDP)
    invoice.lifecycle.add_status(
        InvoiceStatus.RECEIVED,
        date=datetime.utcnow(),
        message="Facture reçue et traitée par la PDP",
    )

    # Enregistrement en mémoire (par session)
    storage_id = store_add(invoice, session_id)

    # Calculs utiles pour l'affichage
    total_ht_calcule = invoice.total_ht_calcule()
    total_ttc_calcule = invoice.total_ttc_calcule()
    total_tva_par_taux = invoice.total_tva_par_taux()
    total_tva_calcule = round(sum(total_tva_par_taux.values()), 2)

    return templates.TemplateResponse(
        "result_invoice.html",
        {
            "request": request,
            "filename": file.filename,
            "raw_content": raw_content,
            "invoice": invoice,
            "decision": decision,
            "anomalies": anomalies,
            "total_ht_calcule": total_ht_calcule,
            "total_ttc_calcule": total_ttc_calcule,
            "total_tva_calcule": total_tva_calcule,
            "total_tva_par_taux": total_tva_par_taux,
            "storage_id": storage_id,
        },
    )


@router.get("/invoices", response_class=HTMLResponse, name="invoices_list")
async def invoices_list(request: Request):
    """Liste des factures de la session en cours."""
    auth = _require_auth(request)
    if isinstance(auth, RedirectResponse):
        return auth
    items = store_list_all(auth)
    return templates.TemplateResponse(
        "invoices_list.html",
        {"request": request, "items": items},
    )


@router.get("/invoices/{storage_id}", response_class=HTMLResponse, name="invoice_detail")
async def invoice_detail(request: Request, storage_id: str):
    """Détail d'une facture + cycle de vie + formulaire ajout de statut."""
    auth = _require_auth(request)
    if isinstance(auth, RedirectResponse):
        return auth
    invoice = store_get(storage_id, auth)
    if invoice is None:
        raise HTTPException(status_code=404, detail="Facture introuvable")

    total_ht_calcule = invoice.total_ht_calcule()
    total_ttc_calcule = invoice.total_ttc_calcule()
    total_tva_par_taux = invoice.total_tva_par_taux()
    total_tva_calcule = round(sum(total_tva_par_taux.values()), 2)
    lifecycle_anomalies = invoice.lifecycle.check_lifecycle()

    return templates.TemplateResponse(
        "invoice_detail.html",
        {
            "request": request,
            "storage_id": storage_id,
            "invoice": invoice,
            "total_ht_calcule": total_ht_calcule,
            "total_ttc_calcule": total_ttc_calcule,
            "total_tva_calcule": total_tva_calcule,
            "total_tva_par_taux": total_tva_par_taux,
            "lifecycle_anomalies": lifecycle_anomalies,
            "status_choices": [
                InvoiceStatus.RECEIVED,
                InvoiceStatus.VALIDATED,
                InvoiceStatus.MISE_EN_PAIEMENT,
                InvoiceStatus.PAYEE,
                InvoiceStatus.REJECTED,
            ],
        },
    )


@router.post("/invoices/{storage_id}/status", name="invoice_add_status")
async def invoice_add_status(
    request: Request,
    storage_id: str,
    statut: str = Form(..., description="Nouveau statut"),
    message: str = Form("", description="Message optionnel"),
):
    """Ajoute un statut à la facture puis redirige vers le détail."""
    auth = _require_auth(request)
    if isinstance(auth, RedirectResponse):
        return auth
    invoice = store_get(storage_id, auth)
    if invoice is None:
        raise HTTPException(status_code=404, detail="Facture introuvable")

    invoice.lifecycle.add_status(statut, date=datetime.utcnow(), message=message or "")

    return RedirectResponse(
        url=request.url_for("invoice_detail", storage_id=storage_id),
        status_code=303,
    )

