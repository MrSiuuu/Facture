from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional


class InvoiceStatus:
    """
    Enumération simple des statuts possibles.
    """

    RECEIVED = "RECEIVED"
    VALIDATED = "VALIDATED"
    MISE_EN_PAIEMENT = "MISE_EN_PAIEMENT"
    PAYEE = "PAYEE"
    REJECTED = "REJECTED"


@dataclass
class StatusChange:
    statut: str
    date: datetime
    message: str = ""


class InvoiceLifecycle:
    """
    Historise les changements de statut d'une facture
    et permet de vérifier le respect des délais réglementaires.
    """

    # Délais maximum par statut (en heures ou jours, selon l'énoncé)
    DELAIS_MAX = {
        InvoiceStatus.RECEIVED: timedelta(hours=24),
        InvoiceStatus.VALIDATED: timedelta(days=7),
        # Pour MISE_EN_PAIEMENT et PAYEE, on simulera ou on utilisera une date d'échéance
    }

    def __init__(self) -> None:
        self.historique: List[StatusChange] = []

    def add_status(self, statut: str, date: Optional[datetime] = None, message: str = "") -> None:
        """
        Ajoute un changement de statut à l'historique.
        """
        if date is None:
            date = datetime.utcnow()
        self.historique.append(StatusChange(statut=statut, date=date, message=message))

    def current_status(self) -> Optional[str]:
        """
        Retourne le dernier statut connu, ou None si aucun.
        """
        if not self.historique:
            return None
        return self.historique[-1].statut

    def is_open(self) -> bool:
        """
        Une facture est ouverte si elle n'est ni PAYEE ni REJECTED.
        """
        statut = self.current_status()
        if statut is None:
            return True
        return statut not in (InvoiceStatus.PAYEE, InvoiceStatus.REJECTED)

    def is_paid(self) -> bool:
        """
        Une facture est payée si son dernier statut est PAYEE.
        """
        return self.current_status() == InvoiceStatus.PAYEE

    def check_lifecycle(self) -> List[str]:
        """
        Vérifie le respect des délais entre statuts.
        Retourne une liste de messages d'anomalies.
        """
        anomalies: List[str] = []

        # Parcours simple des statuts successifs pour illustrer la logique.
        for i in range(len(self.historique) - 1):
            current = self.historique[i]
            suivant = self.historique[i + 1]
            delai = suivant.date - current.date

            max_delai = self.DELAIS_MAX.get(current.statut)
            if max_delai is not None and delai > max_delai:
                anomalies.append(
                    f"Délai dépassé entre {current.statut} et {suivant.statut} : "
                    f"{delai} > {max_delai}"
                )

        return anomalies

