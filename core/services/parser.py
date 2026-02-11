from __future__ import annotations

from datetime import date
from typing import Any, Dict, List

from core.models.invoice import Invoice
from core.models.invoice_line import InvoiceLine
from core.models.party import Party


def _get_first(d: Dict[str, Any], keys: List[str], default: Any = None) -> Any:
    """
    Récupère la première clé présente dans le dict parmi une liste de clés candidates.
    Utile pour s'adapter à différentes variantes de JSON (Factur-X, etc.).
    """
    for key in keys:
        if key in d:
            return d[key]
    return default


def parse_invoice_from_json(data: Dict[str, Any]) -> Invoice:
    """
    Transforme un dictionnaire issu du JSON de facture en objet Invoice.

    Cette implémentation fait quelques hypothèses de structure :
    - Les informations principales sont à la racine ou dans une clé \"invoice\".
    - Le vendeur est dans une clé \"seller\" / \"vendor\".
    - L'acheteur est dans une clé \"buyer\" / \"customer\".
    - Les lignes sont dans \"lines\" / \"invoice_lines\".
    - Les totaux déclarés sont dans \"totals\".

    Ce code sera facilement ajustable dès que l'on connaît la structure exacte
    du JSON Factur-X fourni par le TP.
    """

    # Certains JSON ont un wrapper "invoice"
    root = data.get("invoice", data)

    numero = _get_first(root, ["number", "invoice_number", "id", "numero"], default="UNKNOWN")
    date_str = _get_first(root, ["issue_date", "date", "invoice_date"], default=None)
    if date_str:
        # On suppose un format ISO (YYYY-MM-DD) pour commencer
        date_emission = date.fromisoformat(date_str)
    else:
        # Valeur par défaut "aujourd'hui" si non fournie
        date_emission = date.today()

    devise = _get_first(root, ["currency", "devise", "invoice_currency"], default="EUR")

    # --- Parties prenantes ---
    seller_data = _get_first(root, ["seller", "vendor"], default={}) or {}
    buyer_data = _get_first(root, ["buyer", "customer"], default={}) or {}

    seller = Party(
        identifiant=_get_first(seller_data, ["id", "identifier"], default="SELLER"),
        nom=_get_first(seller_data, ["name", "nom"], default="Vendeur inconnu"),
        adresse=_get_first(seller_data, ["address", "adresse"], default=""),
        pays=_get_first(seller_data, ["country", "pays"], default=""),
        identifiants_fiscaux=_get_first(
            seller_data, ["tax_ids", "identifiants_fiscaux"], default={}
        )
        or {},
    )

    buyer = Party(
        identifiant=_get_first(buyer_data, ["id", "identifier"], default="BUYER"),
        nom=_get_first(buyer_data, ["name", "nom"], default="Acheteur inconnu"),
        adresse=_get_first(buyer_data, ["address", "adresse"], default=""),
        pays=_get_first(buyer_data, ["country", "pays"], default=""),
        identifiants_fiscaux=_get_first(
            buyer_data, ["tax_ids", "identifiants_fiscaux"], default={}
        )
        or {},
    )

    # --- Lignes ---
    raw_lines = _get_first(root, ["lines", "invoice_lines"], default=[]) or []
    lignes: List[InvoiceLine] = []
    for idx, line in enumerate(raw_lines, start=1):
        id_ligne = _get_first(line, ["id", "line_id"], default=str(idx))
        description = _get_first(line, ["description", "designation", "label"], default="")
        quantite = float(_get_first(line, ["quantity", "qty"], default=0.0) or 0.0)
        prix_unitaire = float(
            _get_first(line, ["unit_price", "price_unit"], default=0.0) or 0.0
        )
        montant_ht = float(
            _get_first(
                line,
                ["line_amount_ht", "montant_ht", "amount_ht"],
                default=quantite * prix_unitaire,
            )
            or 0.0
        )
        taux_tva = float(
            _get_first(line, ["vat_rate", "taux_tva"], default=0.0) or 0.0
        )
        categorie_tva = _get_first(
            line, ["vat_category", "categorie_tva"], default=""
        )
        motif_exoneration = _get_first(
            line, ["exemption_reason", "motif_exoneration"], default=None
        )

        lignes.append(
            InvoiceLine(
                id_ligne=id_ligne,
                description=description,
                quantite=quantite,
                prix_unitaire=prix_unitaire,
                montant_ht=montant_ht,
                taux_tva=taux_tva,
                categorie_tva=categorie_tva,
                motif_exoneration=motif_exoneration,
            )
        )

    # --- Totaux déclarés ---
    totals = _get_first(root, ["totals", "montants_declares", "totaux"], default={}) or {}
    montants_declares = {
        "total_ht": float(_get_first(totals, ["total_ht"], default=0.0) or 0.0),
        "total_tva": float(_get_first(totals, ["total_tva"], default=0.0) or 0.0),
        "total_ttc": float(_get_first(totals, ["total_ttc"], default=0.0) or 0.0),
    }

    return Invoice(
        numero=str(numero),
        date_emission=date_emission,
        devise=str(devise),
        seller=seller,
        buyer=buyer,
        lignes=lignes,
        montants_declares=montants_declares,
    )

