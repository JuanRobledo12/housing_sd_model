import numpy as np
import pandas as pd
from scipy.stats import qmc
from mesa import Model, Agent
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector


def compute_gini(model):
    agent_wealths = [agent.wealth for agent in model.agents]
    x = sorted(agent_wealths)
    n = model.num_agents
    B = sum(xi * (n - i) for i, xi in enumerate(x)) / (n * sum(x))
    return 1 + (1 / n) - 2 * B


class MoneyAgent(Agent):
    """An agent with fixed initial wealth."""

    def __init__(self, unique_id, model):
        # Do not call super().__init__()—Mesa’s Agent has no parameters in this version.
        self.unique_id = unique_id
        self.model = model
        self.wealth = 1
        self.pos = None  # so that grid.place_agent(...) can check “if self.pos is not None”

    def move(self):
        possible_steps = self.model.grid.get_neighborhood(
            self.pos, moore=True, include_center=False
        )
        new_position = self.random.choice(possible_steps)
        self.model.grid.move_agent(self, new_position)

    def give_money(self):
        cellmates = self.model.grid.get_cell_list_contents([self.pos])
        cellmates = [a for a in cellmates if a.unique_id != self.unique_id]
        if len(cellmates) > 0 and self.wealth > 0:
            other = self.random.choice(cellmates)
            other.wealth += 1
            self.wealth -= 1

    def step(self):
        """Combined step: move first, then give money."""
        self.move()
        self.give_money()


class MoneyModelSpace(Model):
    """A Mesa Model with n agents on a toroidal grid of size (width × height)."""

    def __init__(self, n, width, height, seed=None):
        super().__init__(seed=seed)
        self.num_agents = n
        self.grid = MultiGrid(width, height, torus=True)

        # DataCollector tracks Gini at each step and each agent’s wealth
        self.datacollector = DataCollector(
            model_reporters={"Gini": compute_gini},
            agent_reporters={"Wealth": "wealth"}
        )

        # Create, place, and register agents
        for i in range(self.num_agents):
            a = MoneyAgent(i, self)
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(a, (x, y))
            self.agents.add(a)  # register agent so self.agents.shuffle_do(...) works

    def step(self):
        # Collect metrics, then have all agents randomly execute their step()
        self.datacollector.collect(self)
        self.agents.shuffle_do("step")

    def run_model(self, n_steps):
        """Helper: run the model for n_steps."""
        for _ in range(n_steps):
            self.step()


def lhs_parameter_sweep(
    n_samples=50,
    n_steps=100,
    param_ranges=None,
    random_seed=None
):
    """
    Perform an LHS sweep over specified parameter ranges
    and return a DataFrame of (parameters + final Gini).
    """
    if param_ranges is None:
        param_ranges = {
            "n":      (10, 200, int),
            "width":  (10, 50, int),
            "height": (10, 50, int),
        }

    D = len(param_ranges)
    sampler = qmc.LatinHypercube(d=D, seed=random_seed)
    unit_samples = sampler.random(n=n_samples)

    dims = list(param_ranges.keys())
    all_param_dicts = []
    for i in range(n_samples):
        sample = unit_samples[i]
        this_params = {}
        for dim_index, dim_name in enumerate(dims):
            low, high, _dtype = param_ranges[dim_name]
            val = low + sample[dim_index] * (high - low)
            if _dtype is int:
                val = int(np.round(val))
            this_params[dim_name] = val
        all_param_dicts.append(this_params)

    results = []
    for idx, pset in enumerate(all_param_dicts):
        n_agents = pset["n"]
        w = pset["width"]
        h = pset["height"]

        model = MoneyModelSpace(n=n_agents, width=w, height=h, seed=random_seed)
        model.run_model(n_steps)

        gini_series = model.datacollector.get_model_vars_dataframe()["Gini"]
        final_gini = gini_series.iloc[-1]

        record = dict(pset)
        record["final_gini"] = final_gini
        results.append(record)

    df_results = pd.DataFrame(results)
    return df_results


if __name__ == "__main__":
    ranges = {
        "n":      (10, 200, int),
        "width":  (10, 50, int),
        "height": (10, 50, int),
    }

    df = lhs_parameter_sweep(
        n_samples=50,
        n_steps=100,
        param_ranges=ranges,
        random_seed=42
    )

    print(df)
