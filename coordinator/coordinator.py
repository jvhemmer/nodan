from dataclasses import dataclass
from uuid import uuid4

from PySide6.QtCore import QPointF

from core.node_system import CoreNode
from core.operations import Operation, ConstantValue, DebugLog, MultiplyValue
from ui.canvas import Canvas
from core.graph import Graph, Executor
from ui.connection import UIConnection
from ui.node import UINode
from ui.port import UIPort


@dataclass
class UINodeBinding:
    core_node: CoreNode
    ui_node: UINode

class Coordinator:
    def __init__(self, canvas: Canvas):
        self.graph = Graph()
        self.canvas = canvas

        self.executor = Executor(self.graph)

        self.node_bindings: dict[str, UINodeBinding] = {}
        self.port_index: dict[UIPort, tuple[str, str, str]] = {}

        self._wire_canvas()

    def _wire_canvas(self) -> None:
        # self.canvas.port_clicked = self.handle_port_clicked
        # self.canvas.node_delete_requested = self.remove_node
        self.canvas.add_node_requested.connect(self.add_node_by_type)

    def add_node_by_type(self, type_id: str, pos: QPointF) -> str:
        # Instantiate the definition
        definition_cls = Operation.registry[type_id]
        definition = definition_cls()

        node = CoreNode(
            id=str(uuid4()),
            definition=definition,
            params=self._default_params(definition),
            state={},
        )
        self.graph.add_node(node)

        ui_node = self._build_ui_node(node, pos)
        self.node_bindings[node.id] = UINodeBinding(core_node=node, ui_node=ui_node)
        return node.id

    def can_connect(self, source_port: UIPort, target_port: UIPort) -> bool:
        source_node_id, source_kind, source_name = self.port_index[source_port]
        target_node_id, target_kind, target_name = self.port_index[target_port]

        if source_kind != "output" or target_kind != "input":
            return False
        if source_node_id == target_node_id:
            return False
        if self._connection_exists(source_node_id, source_name, target_node_id, target_name):
            return False
        if self._input_already_connected(target_node_id, target_name):
            return False
        return True

    def _connection_exists(
            self,
            source_node_id: str,
            source_port: str,
            target_node_id: str,
            target_port: str,
    ) -> bool:
        for connection in self.graph.connections:
            if (
                    connection.source_node_id == source_node_id
                    and connection.source_port == source_port
                    and connection.target_node_id == target_node_id
                    and connection.target_port == target_port
            ):
                return True
        return False

    def _input_already_connected(self, target_node_id: str, target_port: str) -> bool:
        for connection in self.graph.connections:
            if (
                    connection.target_node_id == target_node_id
                    and connection.target_port == target_port
            ):
                return True
        return False

    def connect_ports(self, source: UIPort, target: UIPort) -> None:
        source_node_id, _, source_name = self.port_index[source]
        target_node_id, _, target_name = self.port_index[target]

        # Connect them in Graph
        self.graph.connect(source_node_id, source_name, target_node_id, target_name)

        # Connect them in Canvas
        connection = UIConnection(source, target)
        self.canvas.scene().addItem(connection)
        source.add_connection(connection)
        target.add_connection(connection)

    def remove_node(self, node_id: str) -> None:
        binding = self.node_bindings.pop(node_id, None)
        if binding is None:
            return

        self.graph.connections = [
            c for c in self.graph.connections
            if c.source_node_id != node_id and c.target_node_id != node_id
        ]
        self.graph.nodes.pop(node_id, None)

        for port in binding.ui_node.get_all_ports():
            self.port_index.pop(port, None)

        self.canvas.remove_node(binding.ui_node)

    def update_node_param(self, node_id: str, name: str, value) -> None:
        node = self.graph.nodes[node_id]
        node.params[name] = value
        self.executor.cache.clear()

    def evaluate_node(self, node_id: str) -> dict:
        self.executor.cache.clear()
        result = self.executor.evaluate_node(node_id)
        return result

    def handle_port_clicked(self, port: UIPort) -> None:
        # optional: if you keep pending-drag state in Canvas, Canvas can call
        # coordinator.connect_ports(...) once it has source+target.
        pass

    def _build_ui_node(self, node: CoreNode, pos: QPointF) -> UINode:
        ui_node = UINode(self.canvas, node.id, pos.x(), pos.y(), name=node.definition.title)
        self.canvas.scene().addItem(ui_node)
        self.canvas.nodes.append(ui_node)

        for port in list(ui_node.inputs):
            ui_node.remove_port(port)
        for port in list(ui_node.outputs):
            ui_node.remove_port(port)

        for port_spec in node.definition.get_input_ports(node):
            port = ui_node.add_port("input")
            port.name = port_spec.name
            self.port_index[port] = (node.id, "input", port_spec.name)

        for port_spec in node.definition.outputs:
            port = ui_node.add_port("output")
            port.name = port_spec.name
            self.port_index[port] = (node.id, "output", port_spec.name)

        return ui_node

    def _default_params(self, definition: Operation) -> dict:
        specs = getattr(definition, "params", [])
        return {spec.name: spec.default for spec in specs}