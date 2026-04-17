from core.node_definition import Node, Connection, PortSpec, ParamSpec
from typing import Any

class Graph:
    def __init__(self):
        self.nodes: dict[str, Node] = {}
        self.connections: list[Connection] = []

    def add_node(self, node: Node):
        self.nodes[node.id] = node

    def connect(self, source_node_id: str, source_port: str, target_node_id: str, target_port: str):
        self.connections.append(Connection(source_node_id, source_port, target_node_id, target_port))

class Executor:
    def __init__(self, graph: Graph):
        self.graph = graph
        self.cache: dict[str, dict[str, Any]] = {}

    def evaluate_node(self, node_id: str) -> dict[str, Any]:
        if node_id in self.cache:
            return self.cache[node_id]

        node = self.graph.nodes[node_id]
        resolved_inputs = {}

        for input_spec in node.definition.get_input_ports(node):
            matching_connection = None

            for connection in self.graph.connections:
                # If the current node is the target of a connection,
                # that means there are nodes upstream to evaluate
                is_correct_target_node = connection.target_node_id == node_id
                is_correct_target_port = connection.target_port == input_spec.name

                if is_correct_target_node and is_correct_target_port:
                    matching_connection = connection
                    break

            if matching_connection:
                upstream_outputs = self.evaluate_node(matching_connection.source_node_id)
                resolved_inputs[input_spec.name] = upstream_outputs[matching_connection.source_port]

        outputs = node.definition.evaluate(resolved_inputs, node.params)
        self.cache[node_id] = outputs
        return outputs