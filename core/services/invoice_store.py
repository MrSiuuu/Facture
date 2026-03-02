"""
Store en mémoire des factures traitées, par session.

Chaque session (utilisateur connecté) a son propre espace : à la déconnexion,
ses factures sont supprimées. Pas de BDD.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, List, Optional, Tuple

if TYPE_CHECKING:
    from core.models.invoice import Invoice

# session_id -> (storage_id -> Invoice)
_store_per_session: dict[str, dict[str, "Invoice"]] = {}


def _store_for(session_id: str) -> dict[str, "Invoice"]:
    if session_id not in _store_per_session:
        _store_per_session[session_id] = {}
    return _store_per_session[session_id]


def add(invoice: "Invoice", session_id: str) -> str:
    """
    Enregistre une facture pour la session donnée et retourne son id de stockage.
    """
    storage_id = str(uuid.uuid4())
    _store_for(session_id)[storage_id] = invoice
    return storage_id


def get(storage_id: str, session_id: str) -> Optional["Invoice"]:
    """
    Retourne la facture associée à l'id pour cette session, ou None si inconnu.
    """
    return _store_for(session_id).get(storage_id)


def list_all(session_id: str) -> List[Tuple[str, "Invoice"]]:
    """
    Retourne la liste des (storage_id, invoice) pour cette session.
    """
    return list(_store_for(session_id).items())


def clear_session(session_id: str) -> None:
    """
    Supprime toutes les factures de la session (après déconnexion).
    """
    if session_id in _store_per_session:
        del _store_per_session[session_id]
