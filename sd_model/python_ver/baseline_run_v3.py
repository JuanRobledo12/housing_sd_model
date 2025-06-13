import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
from model_v3 import HousingModel

# Set up paths
DIR_PATH = os.path.dirname(os.path.realpath(__file__))
CONFIG_DIR_PATH = os.path.join(DIR_PATH, "config")
OUTPUT_DIR_PATH = os.path.join(DIR_PATH, "output")
FIGURES_DIR_PATH = os.path.join(OUTPUT_DIR_PATH, "figures")

# Load config file
config_file_name = "config_v3"
CONFIG_FILE_PATH = os.path.join(CONFIG_DIR_PATH, f"{config_file_name}.yaml")

# Initialize the model
hm = HousingModel(CONFIG_FILE_PATH)
config = hm.config
sim_params = config["simulation_parameters"]

# Time settings
houses = sim_params["houses_init"]
sim_time = sim_params["sim_time"]
time_step = sim_params["time_step"]
time_steps = int(sim_time / time_step) + 1
time_range = np.arange(0, sim_time + time_step, time_step)

# Store simulation results
results = {
    "time": [],
    "households": [],
    "houses_to_households_ratio": [],
    "housing_scarcity": [],
    # "effect_of_housing_scarcity_on_cost": [],
    "housing_slack": [],
    # "effect_of_housing_slack_on_cost": [],
    "houses": [],
    "cost_of_housing": [],
    # "private_transportation_investment": [],
    # "public_transportation_investment": [],
    # "time_in_traffic": [],
    "density_index": [],
    # "city_sprawl": [],
    # "access_to_services": [],
}

# Run simulation
for time in time_range:
    housesD, vars = hm.run_step(houses, time, time_step)
    
    # Store results
    results["time"].append(time)
    results["houses"].append(houses)
    results["households"].append(vars["households"])
    results["houses_to_households_ratio"].append(vars["houses_to_households_ratio"])
    results["housing_scarcity"].append(vars["housing_scarcity"])
    # results["effect_of_housing_scarcity_on_cost"].append(vars["effect_of_housing_scarcity_on_cost"])
    results["cost_of_housing"].append(vars["cost_of_housing"])
    results["housing_slack"].append(vars["housing_slack"])
    # results["effect_of_housing_slack_on_cost"].append(vars["effect_of_housing_slack_on_cost"])
    # results["time_in_traffic"].append(vars["time_in_traffic"])
    results["density_index"].append(vars["density_index"])
    # results["private_transportation_investment"].append(vars["private_transportation_investment"])
    # results["public_transportation_investment"].append(vars["public_transportation_investment"])
    # results["city_sprawl"].append(vars["city_sprawl"])
    # results["access_to_services"].append(vars["access_to_services"])
    
    # Update state
    houses += housesD * time_step

# Convert to DataFrame
df = pd.DataFrame(results)

# Plot all columns except 'time'
plot_columns = [col for col in df.columns if col != "time"]
n_cols = 2
n_rows = int(np.ceil(len(plot_columns) / n_cols))

fig, axs = plt.subplots(n_rows, n_cols, figsize=(7 * n_cols, 4 * n_rows))
axs = axs.flatten()

for i, col in enumerate(plot_columns):
    axs[i].plot(df["time"], df[col])
    axs[i].set_title(f"{col.replace('_', ' ').title()} Over Time")

# Hide any unused subplots
for j in range(i + 1, len(axs)):
    fig.delaxes(axs[j])

plt.tight_layout()
plt.show()
plt.savefig(os.path.join(FIGURES_DIR_PATH, "simulation_results.png"))
