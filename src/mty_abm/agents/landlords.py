import mesa


class LandlordAgent(mesa.Agent):
    def __init__(self, unique_id, model, capital, strategy):
        super().__init__(unique_id, model)
        
        # Initialize landlord attributes
        self.capital = capital
        self.strategy = strategy
        self.projects = [] # List of housing projects owned by the landlord
        self.municipality_preferences = {}

    
    def evaluate_projects(self):
        # Placeholder: Evaluate existing housing projects
        pass

    def propose_new_project(self, location):
        # Placeholder: Propose a new housing project at the specified location
        pass

    def request_permit(self, project):
        # Placeholder: Request a permit from the municipality for a new project
        pass

    def develop_project(self, project):
        # Placeholder: Develop the housing project if permit is granted
        pass
    
    def step(self):
        # Placeholder: Evaluate and propose new housing project
        pass