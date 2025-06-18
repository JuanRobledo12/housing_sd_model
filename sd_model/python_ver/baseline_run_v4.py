import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
from model_v4 import HousingModel

# Set up paths
DIR_PATH = os.path.dirname(os.path.realpath(__file__))
CONFIG_DIR_PATH = os.path.join(DIR_PATH, "config")
OUTPUT_DIR_PATH = os.path.join(DIR_PATH, "output")
FIGURES_DIR_PATH = os.path.join(OUTPUT_DIR_PATH, "figures")
BASELINE_SIM_RESULTS_DIR_PATH = os.path.join(OUTPUT_DIR_PATH, "baseline_sim_results")

# Load config file
config_file_name = "config_v4"
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
    "houses": [],
}

# Run simulation
for time in time_range:
    housesD, vars = hm.run_step(houses, time, time_step)
    
    # Store results
    results["time"].append(time)
    results["houses"].append(houses)
    for key, value in vars.items():
        if key not in results:
            results[key] = []
        results[key].append(value)
    
    # Update state
    houses += housesD * time_step

# Convert to DataFrame
df = pd.DataFrame(results)

# # Plot all columns except 'time'
# plot_columns = [col for col in df.columns if col != "time"]
# n_cols = 2
# n_rows = int(np.ceil(len(plot_columns) / n_cols))

# fig, axs = plt.subplots(n_rows, n_cols, figsize=(7 * n_cols, 4 * n_rows))
# axs = axs.flatten()

# for i, col in enumerate(plot_columns):
#     axs[i].plot(df["time"], df[col])
#     axs[i].set_title(f"{col.replace('_', ' ').title()} Over Time")

# # Hide any unused subplots
# for j in range(i + 1, len(axs)):
#     fig.delaxes(axs[j])

# plt.tight_layout()
# plt.show()
# plt.savefig(os.path.join(FIGURES_DIR_PATH, "simulation_results.png"))

# Save results to CSV
output_file_name = f"baseline_sim_results_{config_file_name}.csv"
output_file_path = os.path.join(BASELINE_SIM_RESULTS_DIR_PATH, output_file_name)
os.makedirs(BASELINE_SIM_RESULTS_DIR_PATH, exist_ok=True)
df.to_csv(output_file_path, index=False)
