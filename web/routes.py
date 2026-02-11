import json
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from core.models.lifecycle import InvoiceStatus
from core.services.parser import parse_invoice_from_json
from core.services.facturx_xml import facturx_xml_to_dict
from core.services.validator import validate_invoice
from core.services.invoice_store import add as store_add, get as store_get, list_all as store_list_all


router = APIRouter()
templates = Jinja2Templates(directory="web/templates")


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
    """
    Affiche le formulaire d'upload de facture (JSON ou XML Factur-X).
    """
    return templates.TemplateResponse("upload.html", {"request": request})


@router.post("/process", response_class=HTMLResponse, name="process_invoice")
async def process_invoice(
    request: Request,
    file: UploadFile = File(..., description="Fichier JSON ou XML Factur-X"),
):
    """
    Traite le fichier uploadé (JSON ou XML Factur-X) :
    - parse en dictionnaire Python (conformément à l'énoncé),
    - construit l'objet Invoice,
    - applique les règles de validation métier/fiscales,
    - affiche un résumé complet de la facture.
    """
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

    # Enregistrement en mémoire pour liste et détail
    storage_id = store_add(invoice)

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
    """
    Liste des factures déjà traitées (stockées en mémoire).
    """
    items = store_list_all()
    return templates.TemplateResponse(
        "invoices_list.html",
        {"request": request, "items": items},
    )


@router.get("/invoices/{storage_id}", response_class=HTMLResponse, name="invoice_detail")
async def invoice_detail(request: Request, storage_id: str):
    """
    Détail d'une facture + cycle de vie (historique, is_open, is_paid, check_lifecycle)
    + formulaire pour ajouter un statut.
    """
    invoice = store_get(storage_id)
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
    """
    Ajoute un changement de statut à la facture, puis redirige vers le détail.
    """
    invoice = store_get(storage_id)
    if invoice is None:
        raise HTTPException(status_code=404, detail="Facture introuvable")

    invoice.lifecycle.add_status(statut, date=datetime.utcnow(), message=message or "")

    return RedirectResponse(
        url=request.url_for("invoice_detail", storage_id=storage_id),
        status_code=303,
    )

