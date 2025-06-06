from agents.households import HouseholdAgent
from agents.landlords import LandlordAgent
from agents.municipalities import MunicipalityAgent
from environment.city_graph import CityNetwork 
from mesa import BaseScheduler
import networkx as nx
import mesa


class MonterreyModel(mesa.Model):
    def __init__(self, num_households=10, num_landlords=2, num_municipalities=1):
        super().__init__()
        self.schedule = BaseScheduler(self)
        self.network = nx.grid_2d_graph(5, 5)
        self.pos_map = {i: i for i in range(len(self.network.nodes))}
        mapping = dict(zip(self.network.nodes, range(len(self.network.nodes))))
        self.network = nx.relabel_nodes(self.network, mapping)
        self.grid = CityNetwork(self.network)

        # Create agents
        for i in range(num_households):
            a = HouseholdAgent(i, self, income=self.random.randint(500, 3000), preferences={})
            self.schedule.add(a)
            self.grid.place_agent(a, self.random.choice(list(self.grid.G.nodes)))

        for i in range(num_landlords):
            a = LandlordAgent(i + num_households, self, capital=100000, strategy="infill")
            self.schedule.add(a)

        for i in range(num_municipalities):
            a = MunicipalityAgent(i + num_households + num_landlords, self, budget=10000, policy_alignment=0.7)
            self.schedule.add(a)

    def step(self):
        self.grid.update_service_levels()
        self.schedule.step()
        self.grid.adjust_housing_costs()