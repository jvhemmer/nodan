# NoDAn: Nodal Data Analysis
NoDAn is a desktop application for building data analysis workflows as node diagrams, rather then written scripts. Users create nodes that represent operations such as loading data, filtering columns, multiplying values, plotting results, and inspecting intermediate outputs. Nodes are connected visually, making the data flow easier to understand, adjust, and reuse.

## Features

- Visual node-based workflow editor
- Draggable nodes that represent operations
- Node inputs and outputs modeled as ports that can be connected with lines, representing data/logic flow
- Basic nodes (file reading, constant values, multiplications, plotting, etc.)
- Save/load support

## Installation
This project uses `uv` for dependency management. To install `uv`, see [here](https://docs.astral.sh/uv/getting-started/installation/).

If using Git, clone this repo, install dependencies, and launch `main.py`:
```text
git clone https://github.com/jvhemmer/nodan NoDAn
cd NoDAn
uv sync
uv run nodan
```
