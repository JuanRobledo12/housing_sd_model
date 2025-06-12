import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
from variables_v1 import ModelVariables

# Set up paths
DIR_PATH = os.path.dirname(os.path.realpath(__file__))
CONFIG_DIR_PATH = os.path.join(DIR_PATH, "config")

# Load config file
config_file_name = "config_v1"
CONFIG_FILE_PATH = os.path.join(CONFIG_DIR_PATH, f"{config_file_name}.yaml")

# Initialize the model
mv = ModelVariables(CONFIG_FILE_PATH)
config = mv.config
sim_params = config["simulation_parameters"]

# Time settings
houses = sim_params["houses_init"]
sim_time = sim_params["sim_time"]
time_step = sim_params["time_step"]
time_steps = int(sim_time / time_step) + 1
time_range = np.arange(0, sim_time + time_step, time_step)

# Store simulation results
results = {
    "year": [],
    "houses": [],
    "cost_of_housing": [],
    "time_in_traffic": [],
    "city_sprawl": [],
    "access_to_services": [],
}

# Run simulation
for year in time_range:
    housesD, vars = mv.run(houses)
    
    # Store results
    results["year"].append(year)
    results["houses"].append(houses)
    results["cost_of_housing"].append(vars["cost_of_housing"])
    results["time_in_traffic"].append(vars["time_in_traffic"])
    results["city_sprawl"].append(vars["city_sprawl"])
    results["access_to_services"].append(vars["access_to_services"])
    
    # Update state
    houses += housesD * time_step

# Convert to DataFrame
df = pd.DataFrame(results)

# Plot results
fig, axs = plt.subplots(2, 2, figsize=(14, 10))
axs[0, 0].plot(df["year"], df["houses"])
axs[0, 0].set_title("Housing Stock Over Time")

axs[0, 1].plot(df["year"], df["cost_of_housing"])
axs[0, 1].set_title("Cost of Housing Over Time")

axs[1, 0].plot(df["year"], df["time_in_traffic"])
axs[1, 0].set_title("Avg. Time in Traffic Over Time")

axs[1, 1].plot(df["year"], df["access_to_services"])
axs[1, 1].set_title("Access to Services Over Time")

plt.tight_layout()
plt.show()
