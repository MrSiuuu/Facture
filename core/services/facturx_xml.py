"""
Parse un fichier XML Factur-X (CrossIndustryInvoice) en un dictionnaire Python
normalisé, compatible avec parse_invoice_from_json().

Conformément à l'énoncé : on obtient un "dictionnaire Python" (issu du XML),
puis on réutilise la même logique métier (dict → objets) que pour le JSON.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any, Dict, List


def _text(el: ET.Element | None) -> str:
    """Retourne le texte d'un élément ou une chaîne vide."""
    if el is None:
        return ""
    return (el.text or "").strip()


def _date_from_102(s: str) -> str:
    """Convertit un date au format 102 (YYYYMMDD) en ISO (YYYY-MM-DD)."""
    s = (s or "").strip()
    if len(s) >= 8:
        return f"{s[0:4]}-{s[4:6]}-{s[6:8]}"
    return s


def _build_address(addr: ET.Element | None) -> str:
    """Construit une adresse à partir de PostalTradeAddress."""
    if addr is None:
        return ""
    parts: List[str] = []
    line_one = _text(addr.find("LineOne"))
    line_two = _text(addr.find("LineTwo"))
    postcode = _text(addr.find("PostcodeCode"))
    city = _text(addr.find("CityName"))
    country = _text(addr.find("CountryID"))
    if line_one:
        parts.append(line_one)
    if line_two:
        parts.append(line_two)
    if postcode or city:
        parts.append(f"{postcode} {city}".strip())
    if country:
        parts.append(country)
    return ", ".join(parts)


def _party_from_trade_party(tp: ET.Element | None) -> Dict[str, Any]:
    """Extrait vendeur ou acheteur depuis SellerTradeParty / BuyerTradeParty."""
    if tp is None:
        return {"id": "", "name": "", "address": "", "country": "", "tax_ids": {}}
    addr = tp.find("PostalTradeAddress")
    tax_ids: Dict[str, str] = {}
    for reg in tp.findall("SpecifiedTaxRegistration"):
        scheme = reg.find("ID")
        if scheme is not None and scheme.get("schemeID"):
            tax_ids[scheme.get("schemeID", "")] = _text(scheme)
    return {
        "id": _text(tp.find("ID")),
        "name": _text(tp.find("Name")),
        "address": _build_address(addr),
        "country": _text(addr.find("CountryID")) if addr is not None else "",
        "tax_ids": tax_ids,
    }


def facturx_xml_to_dict(xml_content: str | bytes) -> Dict[str, Any]:
    """
    Parse le XML Factur-X (CrossIndustryInvoice) et retourne un dictionnaire
    normalisé : même structure que celle attendue par parse_invoice_from_json().

    - id / issue_date / currency
    - seller / buyer (id, name, address, country, tax_ids)
    - lines (id, description, quantity, unit_price, montant_ht, vat_rate,
      categorie_tva, exemption_reason)
    - totals (total_ht, total_tva, total_ttc)
    """
    if isinstance(xml_content, bytes):
        xml_content = xml_content.decode("utf-8", errors="replace")
    root = ET.fromstring(xml_content)

    # ExchangedDocument
    doc = root.find("ExchangedDocument")
    doc_id = _text(doc.find("ID")) if doc is not None else ""
    dt_el = doc.find("IssueDateTime/DateTimeString") if doc is not None else None
    date_str = _date_from_102(_text(dt_el)) if dt_el is not None else ""

    # SupplyChainTradeTransaction
    tx = root.find("SupplyChainTradeTransaction")
    if tx is None:
        return {
            "id": doc_id,
            "issue_date": date_str,
            "currency": "EUR",
            "seller": {},
            "buyer": {},
            "lines": [],
            "totals": {"total_ht": 0.0, "total_tva": 0.0, "total_ttc": 0.0},
        }

    agreement = tx.find("ApplicableHeaderTradeAgreement")
    seller = _party_from_trade_party(
        agreement.find("SellerTradeParty") if agreement is not None else None
    )
    buyer = _party_from_trade_party(
        agreement.find("BuyerTradeParty") if agreement is not None else None
    )

    settlement = tx.find("ApplicableHeaderTradeSettlement")
    currency = "EUR"
    if settlement is not None:
        currency_el = settlement.find("InvoiceCurrencyCode")
        if currency_el is not None and currency_el.text:
            currency = currency_el.text.strip()

    # Totaux déclarés
    summation = (
        settlement.find("SpecifiedTradeSettlementHeaderMonetarySummation")
        if settlement is not None
        else None
    )
    total_ht = 0.0
    total_tva = 0.0
    total_ttc = 0.0
    if summation is not None:
        total_ht = float(_text(summation.find("TaxBasisTotalAmount")) or 0.0)
        total_tva = float(_text(summation.find("TaxTotalAmount")) or 0.0)
        total_ttc = float(_text(summation.find("GrandTotalAmount")) or 0.0)

    # Lignes
    lines: List[Dict[str, Any]] = []
    for item in tx.findall("IncludedSupplyChainTradeLineItem"):
        line_id = _text(item.find("AssociatedDocumentLineDocument/LineID"))
        product = item.find("SpecifiedTradeProduct")
        name = _text(product.find("Name")) if product is not None else ""
        desc = _text(product.find("Description")) if product is not None else ""
        description = f"{name} - {desc}".strip(" -") if desc else name

        price_el = item.find(
            "SpecifiedLineTradeAgreement/NetPriceProductTradePrice/ChargeAmount"
        )
        qty_el = item.find("SpecifiedLineTradeDelivery/BilledQuantity")
        unit_price = float(_text(price_el) or 0.0)
        quantity = float(_text(qty_el) or 0.0)

        line_total_el = item.find(
            "SpecifiedLineTradeSettlement/SpecifiedTradeSettlementLineMonetarySummation/LineTotalAmount"
        )
        montant_ht = float(_text(line_total_el) or 0.0)

        tax_el = item.find("SpecifiedLineTradeSettlement/ApplicableTradeTax")
        vat_rate = 0.0
        category = ""
        exemption = None
        if tax_el is not None:
            vat_rate = float(_text(tax_el.find("RateApplicablePercent")) or 0.0)
            category = _text(tax_el.find("CategoryCode"))
            exemption = _text(tax_el.find("ExemptionReason")) or None
            if not exemption:
                exemption = _text(tax_el.find("ExemptionReasonCode")) or None

        lines.append({
            "id": line_id,
            "description": description,
            "quantity": quantity,
            "unit_price": unit_price,
            "montant_ht": montant_ht,
            "vat_rate": vat_rate,
            "categorie_tva": category,
            "exemption_reason": exemption,
        })

    # Dict au format attendu par parse_invoice_from_json (clés utilisées par _get_first)
    return {
        "id": doc_id,
        "issue_date": date_str,
        "currency": currency,
        "seller": seller,
        "buyer": buyer,
        "lines": lines,
        "totals": {
            "total_ht": total_ht,
            "total_tva": total_tva,
            "total_ttc": total_ttc,
        },
    }
