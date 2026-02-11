from __future__ import annotations

from datetime import date
from typing import List, Dict, Optional

from .party import Party
from .invoice_line import InvoiceLine
from .lifecycle import InvoiceLifecycle


class Invoice:
    """
    Représente une facture électronique telle que manipulée par une PDP.

    Regroupe :
    - informations générales (numéro, date d'émission, devise, etc.)
    - vendeur (seller)
    - acheteur (buyer)
    - liste de lignes de facture
    - montants déclarés (HT, TVA, TTC)
    - anomalies détectées
    - décision finale (VALIDATED / REJECTED)
    - cycle de vie (statuts horodatés)
    """

    def __init__(
        self,
        numero: str,
        date_emission: date,
        devise: str,
        seller: Party,
        buyer: Party,
        lignes: List[InvoiceLine],
        montants_declares: Optional[Dict[str, float]] = None,
    ) -> None:
        self.numero = numero
        self.date_emission = date_emission
        self.devise = devise
        self.seller = seller
        self.buyer = buyer
        self.lignes = lignes
        self.montants_declares = montants_declares or {}

        self.anomalies: List[str] = []
        self.decision: Optional[str] = None
        self.lifecycle = InvoiceLifecycle()

    # ---------- Calculs financiers ----------

    def total_ht_calcule(self) -> float:
        """
        Calcule le total HT à partir des lignes.
        """
        return round(sum(l.montant_ht for l in self.lignes), 2)

    def total_tva_par_taux(self) -> Dict[float, float]:
        """
        Calcule la TVA totale par taux de TVA.
        Retourne un dict {taux: montant_tva}.
        """
        totaux: Dict[float, float] = {}
        for ligne in self.lignes:
            montant = ligne.montant_tva()
            totaux[ligne.taux_tva] = totaux.get(ligne.taux_tva, 0.0) + montant
        # Arrondi final par taux
        return {taux: round(montant, 2) for taux, montant in totaux.items()}

    def total_ttc_calcule(self) -> float:
        """
        Calcule le total TTC en sommant le TTC des lignes.
        """
        return round(sum(l.montant_ttc() for l in self.lignes), 2)

    # ---------- Affichage / résumé ----------

    def summary(self) -> str:
        """
        Retourne un résumé lisible de la facture.
        (Utile pour le rapport et pour debug dans la console.)
        """
        lignes_count = len(self.lignes)
        return (
            f"Facture {self.numero} du {self.date_emission.isoformat()} "
            f"({self.devise})\n"
            f"Vendeur : {self.seller.nom} — Acheteur : {self.buyer.nom}\n"
            f"Nombre de lignes : {lignes_count}\n"
            f"Total HT (calculé) : {self.total_ht_calcule()} {self.devise}\n"
            f"Total TTC (calculé) : {self.total_ttc_calcule()} {self.devise}"
        )

