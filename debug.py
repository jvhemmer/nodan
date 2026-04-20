from nodan.core.graph import Graph, Executor
from nodan.core.node_system import CoreNode, DebugLog, ConstantValue, MultiplyValue

graph = Graph()

const_node = CoreNode(
    id="n1",
    definition=ConstantValue(),
    params={"value": 42},
    state={}
)

const_node2 = CoreNode(
    id="n3",
    definition=ConstantValue(),
    params={"value": 100},
    state={}
)

multiply_node = CoreNode(
    id="n4",
    definition=MultiplyValue(),
    params={},
    state={"input_count": 2}
)

log_node = CoreNode(
    id="n2",
    definition=DebugLog(),
    params={},
    state={}
)

log_node2 = CoreNode(
    id="n5",
    definition=DebugLog(),
    params={},
    state={}
)

graph.add_node(const_node)
graph.add_node(const_node2)
graph.add_node(log_node)
graph.add_node(multiply_node)
graph.add_node(log_node2)
graph.connect("n1", "value", "n2", "value")
graph.connect("n1", "value", "n4", "value1")
graph.connect("n3", "value", "n4", "value2")
graph.connect("n4", "result", "n5", "value")


executor = Executor(graph)
executor.evaluate_node("n5")