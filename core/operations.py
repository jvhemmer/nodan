from typing import Any

from core.node_system import PortSpec, RepeatedInputSpec, ParamSpec, Operation

class ConstantValue(Operation):
    type_id = "value.constant"
    title = "Constant"
    category = "Values"

    input_spec = (PortSpec("value", "any", editable=True),)
    output_spec = (PortSpec("value", "any"),)

    def evaluate(self, inputs: dict[str, Any], params: dict[str, Any]) -> dict[str, Any]:
        return {"value": inputs["value"]}


class DebugLog(Operation):
    type_id = "debug.log"
    title = "Debug Log"
    category = "Debug"

    input_spec = (PortSpec("value", "any"))
    output_spec = ()
    params = []

    def evaluate(self, inputs: dict[str, Any], params: dict[str, Any]) -> dict[str, Any]:
        value = inputs["value"]
        print(value)

class MultiplyValue(Operation):
    type_id = "multiply.value"
    title = "Multiply"
    category = "Basic operation"

    repeated_inputs = RepeatedInputSpec(
        base_name="value",
        data_type="number",
        min_count=2,
        default_count=2,
    )

    output_spec = (PortSpec("result", "number"),)

    def evaluate(self, inputs: dict[str, Any], params: dict[str, Any]) -> dict[str, Any]:
        result = 1
        for value in inputs.values():
            result *= float(value)
        return {"result": result}