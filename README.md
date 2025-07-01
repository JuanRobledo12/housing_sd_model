# Housing SD Model

This repository contains early prototypes exploring housing dynamics in two
different ways:

* **System Dynamics (SD) model** – A Python implementation found under
  `sd_model/python_ver`.
* **Agent Based Model (ABM)** – Simple Mesa based examples located in `abm/`.

The SD model focuses on the evolution of housing stock, population, land use
and transportation investment for the municipality of Monterrey.  Parameters
and policy levers are stored in YAML configuration files and can be modified to
explore different scenarios.

## File structure

```
.
├── abm/
│   ├── mty_abm/          # ABM prototype
│   └── tutorials/        # example Mesa models
└── sd_model/
    └── python_ver/
        ├── model_v6.py           # system dynamics model
        ├── baseline_run_v6.py    # baseline simulation script
        ├── scenario_run.py       # helper for scenario runs
        ├── config/               # YAML config files
        └── utils/                # utility functions
```

## Environment set up

1. Create and activate a Python virtual environment (Python 3.8+):

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install the required packages:

   ```bash
   pip install numpy pandas matplotlib pyyaml
   # Optional: required only for the ABM examples
   pip install mesa networkx
   ```

## Using the SD model

### Baseline run

Run `baseline_run_v6.py` to execute the model with the default configuration.
The script saves simulation results as CSV under
`sd_model/python_ver/output/baseline_sim_results`.

```bash
python sd_model/python_ver/baseline_run_v6.py
```

The script loads `model_v6.py`, iterates through time steps and stores the
variables computed by `HousingModel`.

### Scenario simulation

`scenario_run.py` provides a small helper to run the model with any YAML
configuration file:

```python
from sd_model.python_ver.scenario_run import ScenarioRunner

runner = ScenarioRunner("efficient_mty")
df, path = runner.run()
print("Results saved to", path)
```

The runner writes `scenario_sim_results_<config>.csv` to
`sd_model/python_ver/output/scenario_results` and returns the DataFrame with the
results.

## Model description

`model_v6.py` implements the core system dynamics logic. After loading a YAML
file, it simulates housing supply, population growth and land use through a
series of delayed feedback loops:

* Population follows a logistic trend and can emigrate if housing costs rise
  above the starting level.
* Housing costs respond to scarcity or slack and adjust gradually over time
  via a first‑order delay.
* Property taxes generate public funding which influences transport investment,
  proximity and urban sprawl.
* Construction of new houses depends on private investment, financing
  availability and tax effects, with additional delays for stock changes and
  demolition rates.

Model parameters are stored under `sd_model/python_ver/config/` and can be
modified to explore different policy scenarios.
