from __future__ import annotations

from typing import Optional, Dict


class Party:
    """
    Représente une partie prenante de la facture : vendeur ou acheteur.

    Attributs principaux (issus du JSON Factur-X) :
    - identifiant
    - nom
    - adresse
    - pays
    - identifiants fiscaux (TVA, SIREN, etc.)
    """

    def __init__(
        self,
        identifiant: str,
        nom: str,
        adresse: str,
        pays: str,
        identifiants_fiscaux: Optional[Dict[str, str]] = None,
    ) -> None:
        self.identifiant = identifiant
        self.nom = nom
        self.adresse = adresse
        self.pays = pays
        self.identifiants_fiscaux = identifiants_fiscaux or {}

    def __repr__(self) -> str:
        return f"Party(identifiant={self.identifiant!r}, nom={self.nom!r})"

