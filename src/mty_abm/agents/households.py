import mesa

class HouseholdAgent(mesa.Agent):
    def __init__(self, unique_id, model, income):
        super().__init__(unique_id, model)
        
        # Initialize household attributes
        self.income = income
        self.status = "renting"
        self.location = None
        self.cbd_location = None

        # Future attributes can include:
        # self.preferences = {}

    def search_for_housing(self):
        # Placeholder: Implement logic for searching housing
        pass


    def relocate(self, new_location):
        # Placeholder: Implement logic for relocating to a new location
        self.location = new_location

    def exit_housing_market(self):
        # Placeholder: Implement logic for exiting the housing market
        self.status = "homeless"

    
    def step(self):
        # Placeholder: Advance the household's state each step
        pass
