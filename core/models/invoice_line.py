from __future__ import annotations

from typing import Optional


class InvoiceLine:
    """
    Représente une ligne de facture.

    Attributs :
    - id_ligne
    - description
    - quantite
    - prix_unitaire
    - montant_ht
    - taux_tva
    - categorie_tva
    - motif_exoneration (optionnel si taux 0 %)
    """

    def __init__(
        self,
        id_ligne: str,
        description: str,
        quantite: float,
        prix_unitaire: float,
        montant_ht: float,
        taux_tva: float,
        categorie_tva: str,
        motif_exoneration: Optional[str] = None,
    ) -> None:
        self.id_ligne = id_ligne
        self.description = description
        self.quantite = quantite
        self.prix_unitaire = prix_unitaire
        self.montant_ht = montant_ht
        self.taux_tva = taux_tva
        self.categorie_tva = categorie_tva
        self.motif_exoneration = motif_exoneration

    def montant_tva(self) -> float:
        """
        Calcule la TVA de la ligne à partir du montant HT et du taux.
        """
        return round(self.montant_ht * self.taux_tva / 100, 2)

    def montant_ttc(self) -> float:
        """
        Calcule le montant TTC de la ligne.
        """
        return round(self.montant_ht + self.montant_tva(), 2)

    def __repr__(self) -> str:
        return f"InvoiceLine(id_ligne={self.id_ligne!r}, description={self.description!r})"

