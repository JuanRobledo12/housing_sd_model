import mesa


class LandlordAgent(mesa.Agent):
    def __init__(self, unique_id, model, capital, strategy):
        super().__init__(unique_id, model)
        self.capital = capital
        self.strategy = strategy
        self.projects = []

    def step(self):
        # Placeholder: Evaluate and propose new housing project
        pass