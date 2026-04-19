from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from PySide6.QtCore import QPointF

from core.node_system import CoreNode, CorePort, PortSpec
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
            inputs=[],
            outputs=[],
        )
        self.graph.add_node(node)
        node.build_node_ports()

        ui_node = self._build_ui_node(node, pos)
        self.node_bindings[node.id] = UINodeBinding(core_node=node, ui_node=ui_node)
        return node.id

    def can_connect(self, source_port: UIPort, target_port: UIPort) -> bool:
        source_node_id = source_port.ui_node.core_node.id
        source_kind = source_port.core_port.kind
        source_name = source_port.core_port.spec.name

        target_node_id = target_port.ui_node.core_node.id
        target_kind = target_port.core_port.kind
        target_name = target_port.core_port.spec.name

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
        self.graph.connect(
            source.core_port.node_id,
            source.core_port.spec.name,
            target.core_port.node_id,
            target.core_port.spec.name,
        )

        connection = UIConnection(source, target)
        self.canvas.scene().addItem(connection)
        source.add_connection(connection)
        target.add_connection(connection)

    def disconnect_ports(self, source: UIPort, target: UIPort) -> None:
        self.graph.connections = [
            c for c in self.graph.connections
            if not (
                c.source_node_id == source.core_port.node_id
                and c.source_port == source.core_port.spec.name
                and c.target_node_id == target.core_port.node_id
                and c.target_port == target.core_port.spec.name
            )
        ]
        self.executor.cache.clear()


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

    def evaluate_node(self, node: CoreNode) -> dict:
        self.executor.cache.clear()
        result = self.executor.evaluate_node(node.id) # TODO: Change evaluate_node to use CoreNode instead of ID
        return result

    def add_repeated_input(self, node: CoreNode) -> None:
        repeated = node.definition.repeated_inputs
        if repeated is None:
            return

        current_count = node.state.get("input_count", repeated.default_count)
        next_count = current_count + 1
        node.state["input_count"] = next_count

        core_port = CorePort(
            node_id=node.id,
            kind="input",
            spec=PortSpec(
                name=f"{repeated.base_name}{next_count}",
                data_type=repeated.data_type,
                editable=repeated.editable,
            ),
            value=None,
        )
        node.inputs.append(core_port)
        self.executor.cache.clear()

        binding = self.node_bindings.get(node.id)
        if binding is None:
            return

        ui_port = binding.ui_node.add_port("input", core_port)
        ui_port.name = core_port.spec.name

    def remove_repeated_input(self, port: UIPort) -> None:
        if port.kind != "input":
            return

        repeated = port.ui_node.core_node.definition.repeated_inputs
        if repeated is None:
            return

        if port.has_connection():
            return

        node = port.ui_node.core_node
        core_port = port.core_port
        prefix = repeated.base_name

        if not core_port.spec.name.startswith(prefix):
            return

        try:
            index = int(core_port.spec.name.removeprefix(prefix))
        except ValueError:
            return

        current_count = node.state.get("input_count", repeated.default_count)
        if index != current_count or current_count <= repeated.min_count:
            return

        node.inputs.remove(core_port)
        node.state["input_count"] = current_count - 1
        self.executor.cache.clear()
        port.ui_node.remove_port(port)

    def handle_port_clicked(self, port: UIPort) -> None:
        # optional: if you keep pending-drag state in Canvas, Canvas can call
        # coordinator.connect_ports(...) once it has source+target.
        pass

    def _build_ui_node(self, node: CoreNode, pos: QPointF) -> UINode:
        ui_node = UINode(self.canvas, node, pos.x(), pos.y(), name=node.definition.title)
        self.canvas.scene().addItem(ui_node)
        self.canvas.nodes.append(ui_node)

        for port in list(ui_node.inputs):
            ui_node.remove_port(port)
        for port in list(ui_node.outputs):
            ui_node.remove_port(port)

        for core_port in node.inputs:
            print(core_port)
            port = ui_node.add_port("input", core_port)
            port.name = core_port.spec.name

        for core_port in node.outputs:
            print(core_port)
            port = ui_node.add_port("output", core_port)
            port.name = core_port.spec.name

        return ui_node

    def _default_params(self, definition: Operation) -> dict:
        specs = getattr(definition, "params", [])
        return {spec.name: spec.default for spec in specs}

    def set_port_value(self, port: UIPort, raw_value: str) -> None:
        core_port = port.core_port

        if core_port.kind != "input":
            raise ValueError("Only input ports can be edited")

        if not core_port.spec.editable:
            raise ValueError(f"Port '{core_port.spec.name}' is not editable")

        if port.connections:
            raise ValueError(f"Port '{core_port.spec.name}' is connected and cannot be edited")

        core_port.value = self._parse_value(core_port.spec.data_type, raw_value)
        self.executor.cache.clear()

    def _parse_value(self, data_type: str, raw_value: str) -> Any:
        if data_type == "number":
            return float(raw_value) if "." in raw_value else int(raw_value)
        if data_type == "bool":
            return raw_value.strip().lower() in {"1", "true", "yes", "on"}
        if data_type == "string":
            return raw_value
        if data_type == "any":
            return raw_value

        return raw_value
