# Examples

One notebook per use case, mirroring the runnable scripts in
[`tests/examples/`](https://github.com/GOBLIN-Proj/cbm_runner/tree/main/tests/examples).
All four entry points take a scenario or inventory input and produce an annual carbon-flux
DataFrame plus a self-describing SQLite archive (`export_archive()`).

| Notebook | Entry point | Use case |
|----------|-------------|----------|
| [National pipeline](nsg_example.ipynb) | `NationalScenarioGenerator` | Standard national FM + AF + SC to 2070 (internal DB) |
| [Dynamic pipeline](dsg_example.ipynb) | `DynamicScenarioGenerator` | NAI-based continuation beyond 2070 |
| [Standard pipeline](standard_sim_example.ipynb) | `StandardSimGenerator` | User inventory CSVs, static disturbance schedule |
| [Dynamic standard pipeline](dynamic_standard_sim_example.ipynb) | `DynamicStandardSimGenerator` | User CSVs + NAI-based dynamic harvest |

```{note}
The notebooks are rendered as authored (not executed at build time) because each drives a full
CBM simulation that needs the bundled databases and takes minutes to run. To produce live
outputs, run the matching `tests/examples/*.py` script.
```

```{toctree}
:maxdepth: 1
:hidden:

nsg_example.ipynb
dsg_example.ipynb
standard_sim_example.ipynb
dynamic_standard_sim_example.ipynb
```
