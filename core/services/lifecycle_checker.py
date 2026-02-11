from __future__ import annotations

from typing import List

from core.models.invoice import Invoice


def check_invoice_lifecycle(invoice: Invoice) -> List[str]:
    """
    Service simple qui délègue à Invoice.lifecycle.check_lifecycle().
    Séparé pour suivre le plan du projet (service dédié).
    """
    return invoice.lifecycle.check_lifecycle()

