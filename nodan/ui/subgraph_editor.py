from __future__ import annotations
from typing import TYPE_CHECKING

from nodan.core.document import GraphDocument
from nodan.core.node_system import CoreNode
from nodan.core.subgraph import SubgraphDefinition

if TYPE_CHECKING:
    from nodan.coordinator.coordinator import Coordinator

from PySide6.QtWidgets import QWidget


class SubgraphEditor(QWidget):
    def __init__(self, doc: GraphDocument):
        super().__init__()
        self.doc = doc


    #TODO: Show table with name and id of the subgraph and list of nodes.
