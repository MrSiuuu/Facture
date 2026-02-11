"""
Store en mémoire des factures traitées.

Une seule source de vérité (dict) pour les factures enregistrées après POST /process.
Chaque facture est identifiée par un id unique (uuid) pour les URLs.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, List, Optional, Tuple

if TYPE_CHECKING:
    from core.models.invoice import Invoice

# Stockage en mémoire : id (str) -> Invoice
_store: dict[str, "Invoice"] = {}


def add(invoice: "Invoice") -> str:
    """
    Enregistre une facture et retourne son id de stockage.
    """
    storage_id = str(uuid.uuid4())
    _store[storage_id] = invoice
    return storage_id


def get(storage_id: str) -> Optional["Invoice"]:
    """
    Retourne la facture associée à l'id, ou None si inconnu.
    """
    return _store.get(storage_id)


def list_all() -> List[Tuple[str, "Invoice"]]:
    """
    Retourne la liste des (storage_id, invoice) pour affichage.
    Ordre : du plus récent au plus ancien (on n'a pas de date d'ajout, donc ordre d'insertion).
    """
    return list(_store.items())
