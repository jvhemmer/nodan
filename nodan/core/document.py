from __future__ import annotations

from dataclasses import dataclass
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from nodan.coordinator.coordinator import NodeBinding

from nodan.core.graph import Graph
from nodan.core.type_parser import PortValueParser
from nodan.core.node_system import CoreConnection, CoreNode, Operation

@dataclass
class NodeDocument:
    id: str
    type_id: str
    x: float
    y: float
    name: str | None
    state: dict[str, Any]
    input_values: dict[str, Any]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> NodeDocument:
        return cls(
            id=data["id"],
            type_id=data["type_id"],
            x=data.get("x", 0),
            y=data.get("y", 0),
            name=data.get("name"),
            state=dict(data.get("state", {})),
            input_values=dict(data.get("input_values", {})),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type_id": self.type_id,
            "name": self.name,
            "x": self.x,
            "y": self.y,
            "state": self.state,
            "input_values": self.input_values,
        }

    @classmethod
    def from_core(cls, binding: NodeBinding, input_values: dict[str, Any]) -> NodeDocument:
        core_node = binding.core_node
        ui_node = binding.ui_node

        return cls(
            id=core_node.id,
            type_id=core_node.definition.type_id,
            x=ui_node.pos().x(),
            y=ui_node.pos().y(),
            name=ui_node.name,
            state=dict(core_node.state),
            input_values=input_values,
        )

    def to_core(self) -> CoreNode:
        parser = PortValueParser()

        definition_cls = Operation.registry[self.type_id]
        definition = definition_cls()

        node = CoreNode(
            id=self.id,
            definition=definition,
            state=dict(self.state),
            inputs=[],
            outputs=[],
        )
        node.build_node_ports()

        for port_name, raw_value in self.input_values.items():
            port = node.get_input_port(port_name)
            if port is None:
                continue

            #TODO: Make this parsing part of the parser
            if isinstance(raw_value, str):
                port.value = parser.parse(port.spec.data_type, raw_value)
            else:
                port.value = raw_value

        return node


@dataclass(frozen=True)
class ConnectionDocument:
    source_node_id: str
    source_port: str
    target_node_id: str
    target_port: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ConnectionDocument:
        return cls(
            source_node_id=data["source_node_id"],
            source_port=data["source_port"],
            target_node_id=data["target_node_id"],
            target_port=data["target_port"],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_node_id": self.source_node_id,
            "source_port": self.source_port,
            "target_node_id": self.target_node_id,
            "target_port": self.target_port,
        }

    @classmethod
    def from_core(
        cls,
        connection: CoreConnection,
    ) -> ConnectionDocument:
        return cls(
            source_node_id=connection.source_node_id,
            source_port=connection.source_port,
            target_node_id=connection.target_node_id,
            target_port=connection.target_port,
        )

    def to_core(self) -> CoreConnection:
        return CoreConnection(
            source_node_id=self.source_node_id,
            source_port=self.source_port,
            target_node_id=self.target_node_id,
            target_port=self.target_port,
        )

@dataclass
class GraphDocument:
    nodes: list[NodeDocument]
    connections: list[ConnectionDocument]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GraphDocument:
        return cls(
            nodes=[
                NodeDocument.from_dict(node)
                for node in data.get("nodes", [])
            ],
            connections=[
                ConnectionDocument.from_dict(conn)
                for conn in data.get("connections", [])
            ],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": [node.to_dict() for node in self.nodes],
            "connections": [conn.to_dict() for conn in self.connections],
        }

    def to_graph(self) -> Graph:
        graph = Graph()

        for node in self.nodes:
            graph.add_node(node.to_core())

        for connection in self.connections:
            graph.connections.append(connection.to_core())

        return graph


