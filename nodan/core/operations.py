import operator
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
from PySide6.QtWidgets import QFileDialog

from nodan.core.node_system import Operation, PortSpec, RepeatedInputSpec

# TODO: Derivative, Integration, Smoothing


class ConstantValue(Operation):
    type_id = "value.constant"
    name = "Constant"
    category = "Values"

    input_spec = [PortSpec("value", "data", editable=True)]
    output_spec = [PortSpec("value", "data")]

    def evaluate(self, inputs: dict[str, Any]) -> dict[str, Any]:
        return {"value": inputs["value"]}


class DebugLog(Operation):
    type_id = "debug.log"
    name = "Debug Log"
    category = "Debug"

    input_spec = [PortSpec("value", "data")]
    output_spec = []

    def evaluate(self, inputs: dict[str, Any]) -> None:
        print(inputs)


class ElementWiseOperation(Operation):
    operation = staticmethod(operator.add)

    input_spec = []

    repeated_inputs = RepeatedInputSpec(
        name="dataframe",
        data_type="dataframe",
        min_count=2,
        default_count=2,
    )

    output_spec = [PortSpec("result", "dataframe")]

    def evaluate(self, inputs: dict[str, Any]) -> dict[str, Any]:
        dfs = [df for df in inputs.values() if df is not None]
        if not dfs:
            raise ValueError(f"{self.name} requires at least one dataframe.")

        result = dfs[0]
        for df in dfs[1:]:
            result = self.operation(result, df)
        return {"result": result}


class ElementWiseSum(Operation):
    pass


class MultiplyValue(Operation):
    type_id = "value.multiply"
    name = "Multiply"
    category = "Basic operation"

    input_spec = [PortSpec("value", "data")]

    repeated_inputs = RepeatedInputSpec(
        name="value",
        data_type="number",
        min_count=1,
        default_count=1,
    )

    output_spec = [PortSpec("result", "number")]

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
    name = "Read CSV"
    category = "Files"

    input_spec = [
        PortSpec("file_path", "text", editable=True),
        PortSpec("separator", "text", default=",", editable=True),
        PortSpec("comment", "text", default="%", editable=True),
        PortSpec("header", "number", default=None, editable=True),
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
    name = "Filter columns"
    category = "DataFrame"

    input_spec = [PortSpec("dataframe", "dataframe")]

    repeated_inputs = RepeatedInputSpec(
        name="column",
        data_type=["number", "text"],
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


class Find(Operation):
    type_id = "logic.find"
    name = "Find"
    category = "Logic"

    input_spec = [
        PortSpec("condition", "text", editable=True),
        PortSpec("series", "series"),
    ]

    output_spec = [
        PortSpec("index", "data", hideable=True),
        PortSpec("value", "data", hideable=True),
    ]

    def evaluate(self, inputs: dict[str, Any]) -> dict[str, Any]:
        condition = inputs["condition"]
        series = inputs["series"]

        if series is None:
            raise ValueError("Find requires a series input.")
        if not isinstance(condition, str) or not condition.strip():
            raise ValueError("Find requires a non-empty condition.")

        values = self._to_series(series)
        matched_index = []
        matched_values = []

        for idx, val in values.items():
            if self._matches(condition, idx, val):
                matched_index.append(idx)
                matched_values.append(val)

        return {
            "index": pd.Series(matched_index),
            "value": pd.Series(matched_values, index=matched_index),
        }

    # TODO: Replace _to_series() with type coercion by the Executor
    def _to_series(self, value: Any) -> pd.Series:
        if isinstance(value, pd.Series):
            return value

        if isinstance(value, pd.DataFrame):
            if value.shape[1] != 1:
                raise ValueError("Find expects a series or a single-column dataframe.")
            return value.iloc[:, 0]

        return pd.Series(value)

    def _matches(self, condition: str, idx: Any, val: Any) -> bool:
        scope = {"idx": idx, "val": val}
        safe_globals = {"__builtins__": {}}

        try:
            result = eval(condition, safe_globals, scope)
        except Exception as exc:
            raise ValueError(f"Invalid find condition '{condition}': {exc}") from exc

        if not isinstance(result, bool):
            raise ValueError(
                "Find condition must evaluate to a boolean value for each item."
            )

        return result

class PlotXY(Operation):
    type_id = "plot.xy"
    name = "Plot XY"
    category = "Plot"

    input_spec = [
        PortSpec("x", "table"),
        PortSpec("xlabel", "text", editable=True, hideable=True),
        PortSpec("ylabel", "text", editable=True, hideable=True),
        PortSpec("xlim", "text", editable=True, hideable=True),
        PortSpec("ylim", "text", editable=True, hideable=True),
        PortSpec("legend", "text", editable=True, hideable=True),
        PortSpec("stylesheet", "text", editable=True, hideable=True),
        PortSpec("legend_title", "text", editable=True, hideable=True),
  ]

    repeated_inputs = RepeatedInputSpec(
        name="y", data_type="table", min_count=1, default_count=1, editable=True
    )

    output_spec = []

    def evaluate(self, inputs: dict[str, Any]) -> dict[str, Any]:
        x = inputs["x"]
        xlabel = inputs["xlabel"]
        ylabel = inputs["ylabel"]
        xlim = inputs["xlim"]
        ylim = inputs["ylim"]
        legend = inputs["legend"]
        legend_title = inputs["legend_title"]

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

        if xlabel:
            ax.set_xlabel(xlabel)

        if ylabel:
            ax.set_ylabel(ylabel)

        if xlim:
            ax.set_xlim(xlim)

        if ylim:
            ax.set_ylim(ylim)

        if overlay_count > 1:
            if legend:
                ax.legend(legend, title=legend_title)

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
    name = "Execute code"
    category = "Code"

    input_spec = [PortSpec("code", "text", editable=True)]

    repeated_inputs = RepeatedInputSpec(
        name="var", data_type="data", min_count=1, default_count=1, editable=True
    )

    output_spec = []

    def evaluate(self, inputs: dict[str, Any]) -> None:
        code = inputs["code"]

        scope = {
            name: value
            for name, value in inputs.items()
            if name != "code"
        }

        exec(
            "import matplotlib.pyplot as plt\n" +
            "import numpy as np\n" +
            code,
            scope
        )
