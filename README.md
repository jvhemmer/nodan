# NoDAn: Nodal Data Analysis
NoDAn is a desktop application for building data analysis workflows as node diagrams, rather then written scripts. Users create nodes that represent operations such as loading data, filtering columns, multiplying values, plotting results, and inspecting intermediate outputs. Nodes are connected visually, making the data flow easier to understand, adjust, and reuse.

## Features

- Visual node-based workflow editor
- Draggable nodes that represent operations
- Node inputs and outputs modeled as ports that can be connected with lines, representing data/logic flow
- Basic nodes (file reading, constant values, multiplications, plotting, etc.)
- Save/load support

## Roadmap

- Status bar for status and messages
- Custom operations by adding definitions to a file
- Custom node designer that works by combining existing nodes
- Robust typing
- Loops and batch operations
- Advanced figure options
- ~~Basic operations~~

## Installation
This project uses `uv` for dependency management. To install `uv`, see [here](https://docs.astral.sh/uv/getting-started/installation/).

Use [Git](https://git-scm.com/) to clone this repo, install dependencies, and run `nodan`:
```text
git clone https://github.com/jvhemmer/nodan
cd nodan
uv sync
uv run nodan
```
