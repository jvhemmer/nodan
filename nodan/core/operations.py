import operator
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
from PySide6.QtWidgets import QFileDialog

from nodan.core.node_system import Operation, PortSpec, RepeatedInputSpec


class ConstantValue(Operation):
    type_id = "value.constant"
    title = "Constant"
    category = "Values"

    input_spec = [PortSpec("value", "object", editable=True)]
    output_spec = [PortSpec("value", "object")]

    def evaluate(self, inputs: dict[str, Any]) -> dict[str, Any]:
        return {"value": inputs["value"]}


class DebugLog(Operation):
    type_id = "debug.log"
    title = "Debug Log"
    category = "Debug"

    input_spec = [PortSpec("value", "object")]
    output_spec = []

    def evaluate(self, inputs: dict[str, Any]) -> None:
        print(inputs)


class ElementWiseOperation(Operation):
    operation = staticmethod(operator.add)

    input_spec = []

    repeated_inputs = RepeatedInputSpec(
        base_name="dataframe",
        data_type="dataframe",
        min_count=2,
        default_count=2,
    )

    output_spec = [PortSpec("result", "dataframe")]

    def evaluate(self, inputs: dict[str, Any]) -> dict[str, Any]:
        dfs = [df for df in inputs.values() if df is not None]
        if not dfs:
            raise ValueError(f"{self.title} requires at least one dataframe.")

        result = dfs[0]
        for df in dfs[1:]:
            result = self.operation(result, df)
        return {"result": result}


class ElementWiseSum(Operation):
    pass


class MultiplyValue(Operation):
    type_id = "value.multiply"
    title = "Multiply"
    category = "Basic operation"

    input_spec = [PortSpec("value", "object")]

    repeated_inputs = RepeatedInputSpec(
        base_name="value",
        data_type="scalar",
        min_count=1,
        default_count=1,
    )

    output_spec = [PortSpec("result", "scalar")]

    def evaluate(self, inputs: dict[str, Any]) -> dict[str, Any]:
        values = [value for value in inputs.values() if value is not None]
        if not values:
            raise ValueError("Multiply requires at least one input value.")

        result = values[0]
        for value in values[1:]:
            # TODO: Check type correctly rather then convert
            result = result * float(value)
        return {"result": result}


class ReadCSV(Operation):
    type_id = "file.read_csv"
    title = "Read CSV"
    category = "Files"

    input_spec = [
        PortSpec("file_path", "text", editable=True),
        PortSpec("separator", "text", default=",", editable=True),
        PortSpec("comment", "text", default="%", editable=True),
        PortSpec("header", "scalar", default=None, editable=True),
    ]
    output_spec = [PortSpec("result", "dataframe")]

    def evaluate(self, inputs: dict[str, Any]) -> dict[str, Any]:
        file_path = inputs["file_path"]
        separator = inputs["separator"]
        comment = inputs["comment"]
        header = int(inputs["header"]) if inputs["header"] is not None else None

        if file_path is None:
            file_path = QFileDialog.getOpenFileName()[0]
            if not file_path:
                raise ValueError("No file selected for opening.")

        csv = pd.read_csv(file_path, sep=separator, comment=comment, header=header)

        return {"result": csv}


class FilterColumns(Operation):
    type_id = "filter.dataframe"
    title = "Filter columns"
    category = "DataFrame"

    input_spec = [PortSpec("dataframe", "dataframe")]

    repeated_inputs = RepeatedInputSpec(
        base_name="column",
        data_type="object",
        min_count=1,
        default_count=1,
        editable=True,
    )

    output_spec = [PortSpec("result", "dataframe")]

    def evaluate(self, inputs: dict[str, Any]) -> dict[str, Any]:
        df = inputs["dataframe"]
        columns = [value for name, value in inputs.items() if name.startswith("column")]

        if all(isinstance(col, int) for col in columns):
            filtered = df.iloc[:, columns]
        else:
            filtered = df.loc[:, columns]

        return {"result": filtered}


class PlotXY(Operation):
    type_id = "plot.xy"
    title = "Plot XY"
    category = "Plot"

    input_spec = [PortSpec("x", "object")]

    repeated_inputs = RepeatedInputSpec(
        base_name="y", data_type="object", min_count=1, default_count=1, editable=True
    )

    output_spec = []

    def evaluate(self, inputs: dict[str, Any]) -> dict[str, Any]:
        x = inputs["x"]
        ys = [
            value
            for name, value in sorted(
                (
                    (name, value)
                    for name, value in inputs.items()
                    if name.startswith("y")
                ),
                key=lambda item: int(item[0].removeprefix("y")),
            )
            if value is not None
        ]

        if not ys:
            raise ValueError("PlotXY requires at least one y input.")

        x_values = self._to_plot_values(x)
        fig, ax = plt.subplots()

        overlay_count = 0
        for y in ys:
            for label, y_values in self._extract_series(y):
                if len(x_values) != len(y_values):
                    raise ValueError("x and y must have the same length.")

                if label is None:
                    label = f"y{overlay_count + 1}"
                ax.plot(x_values, y_values, label=label)
                overlay_count += 1

        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.set_title("Plot XY")

        if overlay_count > 1:
            ax.legend()

        fig.tight_layout()
        plt.show()

        return {}

    def _to_plot_values(self, value: Any) -> list[Any]:
        if isinstance(value, pd.DataFrame):
            if value.shape[1] != 1:
                raise ValueError(
                    "PlotXY x input must be a Series or single-column DataFrame."
                )
            return value.iloc[:, 0].tolist()
        if isinstance(value, pd.Series):
            return value.tolist()
        if hasattr(value, "tolist"):
            converted = value.tolist()
            if isinstance(converted, list):
                return converted
        if isinstance(value, (list, tuple)):
            return list(value)
        raise ValueError("PlotXY input must be array-like.")

    def _extract_series(self, value: Any) -> list[tuple[str | None, list[Any]]]:
        if isinstance(value, pd.DataFrame):
            return [(str(column), value[column].tolist()) for column in value.columns]
        if isinstance(value, pd.Series):
            label = str(value.name) if value.name is not None else None
            return [(label, value.tolist())]
        return [(None, self._to_plot_values(value))]


class RawCode(Operation):
    type_id = "code.execute"
    title = "Execute code"
    category = "Code"

    input_spec = [PortSpec("code", "text", editable=True)]

    output_spec = []

    def evaluate(self, inputs: dict[str, Any]) -> None:
        text = inputs["code"]
        eval(text)
