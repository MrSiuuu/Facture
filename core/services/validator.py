from __future__ import annotations

from typing import Dict, List, Tuple

from core.models.invoice import Invoice
from core.models.lifecycle import InvoiceStatus


TOLERANCE = 0.01  # tolérance sur les comparaisons de montants


def _ecart_significatif(attendu: float, calcule: float, tolerance: float = TOLERANCE) -> bool:
    return abs(attendu - calcule) > tolerance


def validate_invoice_financials(invoice: Invoice) -> List[str]:
    """
    Règles de cohérence financière :
    - total HT calculé vs déclaré
    - total TVA calculé vs déclaré
    - total TTC calculé vs déclaré
    """
    anomalies: List[str] = []

    total_ht_calcule = invoice.total_ht_calcule()
    total_tva_par_taux = invoice.total_tva_par_taux()
    total_tva_calcule = round(sum(total_tva_par_taux.values()), 2)
    total_ttc_calcule = invoice.total_ttc_calcule()

    total_ht_decl = float(invoice.montants_declares.get("total_ht", 0.0))
    total_tva_decl = float(invoice.montants_declares.get("total_tva", 0.0))
    total_ttc_decl = float(invoice.montants_declares.get("total_ttc", 0.0))

    if _ecart_significatif(total_ht_decl, total_ht_calcule):
        anomalies.append(
            f"Écart total HT (déclaré={total_ht_decl}, calculé={total_ht_calcule})"
        )
    if _ecart_significatif(total_tva_decl, total_tva_calcule):
        anomalies.append(
            f"Écart total TVA (déclaré={total_tva_decl}, calculé={total_tva_calcule})"
        )
    if _ecart_significatif(total_ttc_decl, total_ttc_calcule):
        anomalies.append(
            f"Écart total TTC (déclaré={total_ttc_decl}, calculé={total_ttc_calcule})"
        )

    return anomalies


def validate_vat_and_exemptions(invoice: Invoice) -> List[str]:
    """
    Règles de TVA :
    - Regrouper les lignes par taux de TVA (via total_tva_par_taux pour les montants)
    - Vérifier qu'une TVA à 0% a un motif explicite d'exonération.
    """
    anomalies: List[str] = []

    # Vérification de la TVA à 0 % avec motif
    for ligne in invoice.lignes:
        if ligne.taux_tva == 0 and not (ligne.motif_exoneration or "").strip():
            anomalies.append(
                f"Ligne {ligne.id_ligne} : TVA 0% sans motif d'exonération renseigné."
            )

    # Si le JSON déclare des montants de TVA par taux, on peut comparer
    declares_par_taux: Dict[str, float] = invoice.montants_declares.get(
        "tva_par_taux", {}
    )  # type: ignore[assignment]
    if isinstance(declares_par_taux, dict) and declares_par_taux:
        calc_par_taux = invoice.total_tva_par_taux()
        for taux, montant_calc in calc_par_taux.items():
            key = str(taux)
            montant_decl = float(declares_par_taux.get(key, 0.0))
            if _ecart_significatif(montant_decl, montant_calc):
                anomalies.append(
                    f"Écart TVA pour le taux {taux}% (déclaré={montant_decl}, calculé={montant_calc})"
                )

    return anomalies


def validate_lifecycle(invoice: Invoice) -> List[str]:
    """
    Règles sur le cycle de vie :
    - Utilise Invoice.lifecycle.check_lifecycle() pour détecter les dépassements de délais.
    - Applique les règles de conformité globale :
      * facture conforme si toutes les étapes sont dans les délais et
        si elle est PAYEE ou en cours sans dépassement.
      * facture en anomalie si un délai est dépassé.
      * facture rejetée si statut REJECTED.
    """
    anomalies: List[str] = []

    # Anomalies de délais
    anomalies.extend(invoice.lifecycle.check_lifecycle())

    # Statut REJECTED explicite
    statut_courant = invoice.lifecycle.current_status()
    if statut_courant == InvoiceStatus.REJECTED:
        anomalies.append("Statut REJECTED : la facture est rejetée.")

    return anomalies


def validate_invoice(invoice: Invoice) -> Tuple[str, List[str]]:
    """
    Moteur de validation global :
    - applique les règles financières,
    - les règles TVA / exonérations,
    - les règles de cycle de vie,
    - retourne (décision, liste_d_anomalies).

    Décision :
    - \"VALIDATED\" si aucune anomalie,
    - \"REJECTED\" sinon.
    """
    anomalies: List[str] = []
    anomalies.extend(validate_invoice_financials(invoice))
    anomalies.extend(validate_vat_and_exemptions(invoice))
    anomalies.extend(validate_lifecycle(invoice))

    if anomalies:
        decision = "REJECTED"
    else:
        decision = "VALIDATED"

    invoice.anomalies = anomalies
    invoice.decision = decision

    return decision, anomalies

