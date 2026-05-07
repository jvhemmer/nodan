from typing import Any

from nodan.core.node_system import CoreConnection, CoreNode


class Graph:
    def __init__(self):
        self.nodes: dict[str, CoreNode] = {}
        self.connections: list[CoreConnection] = []

    def add_node(self, node: CoreNode):
        self.nodes[node.id] = node

    def connect(
        self,
        source_node_id: str,
        source_port: str,
        target_node_id: str,
        target_port: str,
    ):
        self.connections.append(
            CoreConnection(source_node_id, source_port, target_node_id, target_port)
        )

    def disconnect(
            self,
            source_node_id: str,
            source_port: str,
            target_node_id: str,
            target_port: str,
    ) -> None:
        self.connections = [
            connection for connection in self.connections
            if not (
                    connection.source_node_id == source_node_id
                    and connection.source_port == source_port
                    and connection.target_node_id == target_node_id
                    and connection.target_port == target_port
            )
        ]

    def incoming_connections(
            self,
            node_id: str,
            port_name: str | None = None,
    ) -> list[CoreConnection]:
        return [
            connection
            for connection in self.connections
            if connection.target_node_id == node_id
               and (port_name is None or connection.target_port == port_name)
        ]

    def outgoing_connections(
        self,
        node_id: str,
        port_name: str | None = None,
    ) -> list[CoreConnection]:
        return [
            connection
            for connection in self.connections
            if connection.source_node_id == node_id
            and (port_name is None or connection.source_port == port_name)
        ]

    def input_port_is_connected(self, node_id: str, port_name: str) -> bool:
        return any(
            connection.target_node_id == node_id
            and connection.target_port == port_name
            for connection in self.connections
        )

    def output_port_is_connected(self, node_id: str, port_name: str) -> bool:
        return any(
            connection.source_node_id == node_id
            and connection.source_port == port_name
            for connection in self.connections
        )

    def connection_exists(
            self,
            source_node_id: str,
            source_port: str,
            target_node_id: str,
            target_port: str,
    ) -> bool:
        return any(
            connection.source_node_id == source_node_id
            and connection.source_port == source_port
            and connection.target_node_id == target_node_id
            and connection.target_port == target_port
            for connection in self.connections
        )

    def get_input_connection(self, node_id: str, port_name: str) -> CoreConnection | None:
        for connection in self.connections:
            if (
                connection.target_node_id == node_id
                and connection.target_port == port_name
            ):
                return connection
        return None


class Executor:
    def __init__(self, graph: Graph):
        self.graph = graph
        self.cache: dict[str, dict[str, Any]] = {}

    def evaluate_node(self, node_id: str) -> dict[str, Any] | None:
        if node_id in self.cache:
            return self.cache[node_id]

        node = self.graph.nodes[node_id]
        resolved_inputs: dict[str, Any] = {}

        for input_port in node.inputs:
            input_name = input_port.spec.name
            matching_connection = self.graph.get_input_connection(node_id, input_name)

            if matching_connection is not None:
                upstream_outputs = self.evaluate_node(
                    matching_connection.source_node_id
                )
                if upstream_outputs is None:
                    return None

                value = upstream_outputs[matching_connection.source_port]
                input_port.value = value
                resolved_inputs[input_name] = value
                continue

            resolved_inputs[input_name] = input_port.value

        outputs = node.definition.evaluate(resolved_inputs)

        if outputs is not None:
            for output_port in node.outputs:
                output_port.value = outputs.get(output_port.spec.name)

            self.cache[node_id] = outputs
            return outputs
