import json
import keyword
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from PySide6.QtCore import QPointF

from nodan.core.graph import Executor, Graph
from nodan.core.node_system import CoreConnection, CoreNode, CorePort, PortSpec
from nodan.core.operations import Operation

from nodan.core.type_parser import PortValueParser
from nodan.ui.canvas import Canvas
from nodan.ui.connection import UIConnection
from nodan.ui.node import UINode
from nodan.ui.port import UIPort


@dataclass
class UINodeBinding:
    core_node: CoreNode
    ui_node: UINode


class Coordinator:
    def __init__(self, canvas: Canvas):
        self.graph = Graph()
        self.canvas = canvas

        self.executor = Executor(self.graph)
        self.value_parser = PortValueParser()

        self.node_bindings: dict[str, UINodeBinding] = {}
        self.port_index: dict[UIPort, tuple[str, str, str]] = {}

        self._wire_canvas()

    def _wire_canvas(self) -> None:
        # self.canvas.port_clicked = self.handle_port_clicked
        # self.canvas.node_delete_requested = self.remove_node
        self.canvas.add_node_requested.connect(self.add_node_by_type)

    def add_node_by_type(self, type_id: str, pos: QPointF) -> str:
        node = self._create_node(type_id, pos)
        return node.id

    def _create_node(
        self,
        type_id: str,
        pos: QPointF,
        *,
        node_id: str | None = None,
        state: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        ui_name: str | None = None,
    ) -> CoreNode:
        # Instantiate the definition
        definition_cls = Operation.registry[type_id]
        definition = definition_cls()

        node = CoreNode(
            id=node_id or str(uuid4()),
            definition=definition,
            params=params or self._default_params(definition),
            state=dict(state or {}),
            inputs=[],
            outputs=[],
        )
        self.graph.add_node(node)
        node.build_node_ports()

        ui_node = self._build_ui_node(node, pos)
        if ui_name is not None:
            ui_node.change_label(ui_name)
        self.node_bindings[node.id] = UINodeBinding(core_node=node, ui_node=ui_node)
        return node

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
        if self._connection_exists(
            source_node_id, source_name, target_node_id, target_name
        ):
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
        source.ui_node.sync_port_widgets()
        target.ui_node.sync_port_widgets()

    def disconnect_ports(self, source: UIPort, target: UIPort) -> None:
        self.graph.connections = [
            c
            for c in self.graph.connections
            if not (
                c.source_node_id == source.core_port.node_id
                and c.source_port == source.core_port.spec.name
                and c.target_node_id == target.core_port.node_id
                and c.target_port == target.core_port.spec.name
            )
        ]
        self.executor.cache.clear()
        source.ui_node.sync_port_widgets()
        target.ui_node.sync_port_widgets()

    def remove_node(self, node_id: str) -> None:
        binding = self.node_bindings.pop(node_id, None)
        if binding is None:
            return

        self.graph.connections = [
            c
            for c in self.graph.connections
            if c.source_node_id != node_id and c.target_node_id != node_id
        ]
        self.graph.nodes.pop(node_id, None)

        for port in binding.ui_node.get_all_ports():
            self.port_index.pop(port, None)

        self.canvas.remove_node(binding.ui_node)

    def clear(self) -> None:
        for node_id in list(self.node_bindings.keys()):
            self.remove_node(node_id)
        self.graph.connections.clear()
        self.graph.nodes.clear()
        self.executor.cache.clear()
        self.canvas.clear_pending_connection()

    def update_node_param(self, node_id: str, name: str, value) -> None:
        node = self.graph.nodes[node_id]
        node.params[name] = value
        self.executor.cache.clear()

    def evaluate_node(self, node: CoreNode) -> dict | None:
        self.executor.cache.clear()
        result = self.executor.evaluate_node(
            node.id
        )  # TODO: Change evaluate_node to use CoreNode instead of ID
        self._refresh_all_nodes()
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
                name=f"{repeated.name}{next_count}",
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
        fixed_input_count = len(node.definition.input_spec)
        repeated_ports = node.inputs[fixed_input_count:]
        if core_port not in repeated_ports:
            return

        if len(repeated_ports) <= repeated.min_count:
            return

        node.inputs.remove(core_port)
        self.executor.cache.clear()
        port.ui_node.remove_port(port)

    def _build_ui_node(self, node: CoreNode, pos: QPointF) -> UINode:
        ui_node = UINode(
            self.canvas, node, pos.x(), pos.y(), name=node.definition.title
        )
        self.canvas.scene().addItem(ui_node)
        self.canvas.nodes.append(ui_node)

        for port in list(ui_node.inputs):
            ui_node.remove_port(port)
        for port in list(ui_node.outputs):
            ui_node.remove_port(port)

        for core_port in node.inputs:
            port = ui_node.add_port("input", core_port)
            port.name = core_port.spec.name

        for core_port in node.outputs:
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
            raise ValueError(
                f"Port '{core_port.spec.name}' is connected and cannot be edited"
            )

        core_port.value = self.value_parser.parse(core_port.spec.data_type, raw_value)
        self.executor.cache.clear()
        port.ui_node.sync_port_widgets()

    def rename_port(self, port: UIPort, raw_name: str) -> None:
        core_port = port.core_port
        node = port.ui_node.core_node
        repeated = node.definition.repeated_inputs

        if port.kind != "input" or repeated is None:
            raise ValueError("Only repeated input ports can be renamed")

        min_count = repeated.min_count
        repeated_ports = node.inputs[min_count:]
        if core_port not in repeated_ports:
            raise ValueError("Only user-added repeated input ports can be renamed")

        new_name = raw_name.strip()
        if not new_name:
            raise ValueError("Port name cannot be empty")
        if not new_name.isidentifier() or keyword.iskeyword(new_name):
            raise ValueError(f"Invalid port name '{new_name}'")

        old_name = core_port.spec.name
        if new_name == old_name:
            return

        if node.get_input_port(new_name) is not None:
            raise ValueError(f"Input port '{new_name}' already exists")

        core_port.spec.name = new_name
        port.name = new_name

        for connection in self.graph.connections:
            if connection.target_node_id == node.id and connection.target_port == old_name:
                connection.target_port = new_name

        self.executor.cache.clear()
        port.ui_node.sync_port_widgets()

    def _refresh_all_nodes(self) -> None:
        for binding in self.node_bindings.values():
            binding.ui_node.sync_port_widgets()

    def _find_ui_port(self, ports: list[UIPort], port_name: str) -> UIPort | None:
        for port in ports:
            if port.core_port.spec.name == port_name:
                return port
        return None

    # === Subgraphs ===

    # === Save/load and (de)serialization ===
    def save_to_file(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as file:
            json.dump(self.serialize_graph(), file, indent=2)

    def load_from_file(self, path: str) -> None:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
        self.load_graph(data)

    def serialize_graph(self) -> dict[str, Any]:
        return {
            "nodes": [
                self._serialize_node(binding.core_node)
                for binding in self.node_bindings.values()
            ],
            "connections": [
                self._serialize_connection(connection)
                for connection in self.graph.connections
            ],
        }

    def load_graph(self, data: dict[str, Any]) -> None:
        self.clear()

        for node_data in data.get("nodes", []):
            node = self._create_node(
                node_data["type_id"],
                QPointF(node_data.get("x", 0), node_data.get("y", 0)),
                node_id=node_data["id"],
                state=node_data.get("state", {}),
                params=node_data.get("params", {}),
                ui_name=node_data.get("name"),
            )

            input_values = node_data.get("input_values", {})
            for port_name, value in input_values.items():
                port = node.get_input_port(port_name)
                if port is not None:
                    if isinstance(value, str):
                        port.value = self.value_parser.parse(port.spec.data_type, value)
                    else:
                        port.value = value

            binding = self.node_bindings[node.id]
            binding.ui_node.sync_port_widgets()

        for connection_data in data.get("connections", []):
            source_binding = self.node_bindings.get(connection_data["source_node_id"])
            target_binding = self.node_bindings.get(connection_data["target_node_id"])
            if source_binding is None or target_binding is None:
                continue

            source_port = self._find_ui_port(
                source_binding.ui_node.outputs, connection_data["source_port"]
            )
            target_port = self._find_ui_port(
                target_binding.ui_node.inputs, connection_data["target_port"]
            )
            if source_port is None or target_port is None:
                continue

            self.connect_ports(source_port, target_port)

        self._refresh_all_nodes()

    def _serialize_node(self, node: CoreNode) -> dict[str, Any]:
        binding = self.node_bindings[node.id]
        ui_node = binding.ui_node
        local_input_values = {
            port.spec.name: self._serialize_value(port.value)
            for port in node.inputs
            if port.spec.editable
            and not self._input_already_connected(node.id, port.spec.name)
        }

        return {
            "id": node.id,
            "type_id": node.definition.type_id,
            "name": ui_node.name,
            "x": ui_node.pos().x(),
            "y": ui_node.pos().y(),
            "state": node.state,
            "params": node.params,
            "input_values": local_input_values,
        }

    def _serialize_connection(self, connection: CoreConnection) -> dict[str, Any]:
        return {
            "source_node_id": connection.source_node_id,
            "source_port": connection.source_port,
            "target_node_id": connection.target_node_id,
            "target_port": connection.target_port,
        }

    def _serialize_port_spec(self, port: PortSpec) -> dict[str, Any]:
        return {
            "name": port.name,
            "data_type": port.data_type,
            "default": self._serialize_value(port.default),
            "editable": port.editable,
            "hideable": port.hideable,
        }

    def _deserialize_port_spec(self, data: dict[str, Any]) -> PortSpec:
        return PortSpec(
            name=data["name"],
            data_type=data["data_type"],
            default=data.get("default"),
            editable=data.get("editable", False),
            hideable=data.get("hideable", False),
        )

    def _serialize_value(self, value: Any) -> Any:
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, list):
            return [self._serialize_value(item) for item in value]
        if isinstance(value, dict):
            return {key: self._serialize_value(item) for key, item in value.items()}
        raise TypeError(f"Cannot serialize value of type {type(value).__name__}")
