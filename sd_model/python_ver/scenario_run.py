import numpy as np
import pandas as pd
import os
from model_v6 import HousingModel

class ScenarioRunner:
    def __init__(self, config_file_name, base_dir=None):
        self.base_dir = base_dir or os.path.dirname(os.path.realpath(__file__))
        self.config_dir = os.path.join(self.base_dir, "config")
        self.output_dir = os.path.join(self.base_dir, "output")
        self.figures_dir = os.path.join(self.output_dir, "figures")
        self.results_dir = os.path.join(self.output_dir, "scenario_results")
        self.config_file_name = config_file_name
        self.config_file_path = os.path.join(self.config_dir, f"{config_file_name}.yaml")
        self.hm = HousingModel(self.config_file_path)
        self.config = self.hm.config
        self.sim_params = self.config["simulation_parameters"]

    def run(self):
        houses = self.sim_params["houses_init"]
        sim_time = self.sim_params["sim_time"]
        time_step = self.sim_params["time_step"]
        time_range = np.arange(0, sim_time + time_step, time_step)

        results = {
            "time": [],
            "houses": [],
        }

        for time in time_range:
            housesD, vars = self.hm.run_step(houses, time, time_step)
            results["time"].append(time)
            results["houses"].append(houses)
            for key, value in vars.items():
                if key not in results:
                    results[key] = []
                results[key].append(value)
            houses += housesD * time_step

        df = pd.DataFrame(results)
        output_file_name = f"scenario_sim_results_{self.config_file_name}.csv"
        output_file_path = os.path.join(self.results_dir, output_file_name)
        os.makedirs(self.results_dir, exist_ok=True)
        df.to_csv(output_file_path, index=False)
        return df, output_file_path

# Example usage:
# runner = ScenarioRunner("config_v6")
# df, path = runner.run()
