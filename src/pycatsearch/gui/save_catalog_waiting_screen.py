from os import PathLike

from qtpy.QtCore import QCoreApplication, QMargins
from qtpy.QtWidgets import QWidget

from .waiting_screen import WaitingScreen
from ..utils import CatalogType, save_catalog_to_file

__all__ = ["SaveCatalogWaitingScreen"]


class SaveCatalogWaitingScreen(WaitingScreen):
    def __new__(
        cls,
        parent: QWidget | None,
        *,
        filename: str | PathLike[str],
        catalog: CatalogType,
        frequency_limits: tuple[float, float],
        margins: int | QMargins | None = None,
    ) -> WaitingScreen:
        return WaitingScreen(
            parent=parent,
            label=QCoreApplication.translate("SaveCatalogWaitingScreen", "Please wait…"),
            target=save_catalog_to_file,
            kwargs=dict(filename=filename, catalog=catalog, frequency_limits=frequency_limits),
            margins=margins,
        )
