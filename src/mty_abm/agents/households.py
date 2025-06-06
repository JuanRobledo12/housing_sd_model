import mesa

class HouseholdAgent(mesa.Agent):
    def __init__(self, unique_id, model, income, preferences):
        super().__init__(unique_id, model)
        self.income = income
        self.preferences = preferences
        self.status = "renting"
        self.location = None

    def step(self):
        # Placeholder: Household decides whether to move or stay
        pass
