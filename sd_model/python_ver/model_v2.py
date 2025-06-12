from utils.utils import Utils
import numpy as np

class HousingModel:

    def __init__(self, config_yaml_path: str):

        # Initialize an instance of Utils to load the YAML file
        self.u = Utils()
        self.config_yaml_path = config_yaml_path
        self.config = self.load_config_file()

    def load_config_file(self) -> dict:
        """
        Loads the configuration file specified by `self.config_yaml_path` using the utility's `load_yaml` method.
        Returns:
            dict: The contents of the configuration file as a dictionary.
        """
        
        return self.u.load_yaml(self.config_yaml_path)
    

    def calculate_model_variables(self, houses, time) -> dict:
        """
        Calculates and returns a dictionary of model variables based on the current housing stock and model configuration.
        This method computes a variety of intermediate and output variables used in the system dynamics housing model, including variables related to housing, financing, taxes, funding, transportation investment, land use, services investment, and construction. The calculations use model parameters and policies provided in the configuration, as well as utility functions for mathematical transformations.
        Args:
            houses (float or int): The current number of houses (housing stock) in the model.
            time (float): The current time in the model, used for dynamic calculations.
        Returns:
            dict: A dictionary containing all computed model variables.
        Notes:
            - Some variables are marked as model outputs.
            - Some calculations are noted as TODOs for future improvements (e.g., adding delay effects).
            - Utility functions (self.u) are used for mathematical transformations such as elasticity, Michaelis-Menten, exponential growth, and logistic functions.
        """
    
        # load config setup from the YAML file
        parameters = self.config["model_parameters"]
        policies = self.config["model_policies"]
        funct_params = self.config["response_function_parameters"]

        # Initialize an empty dictionary to store model variables
        model_variables = {}
        
       
       # Define population as a function of time
        P0 = parameters["initial_pop"]
        r  = funct_params["pop_growth_rate"]

        # log1p ensures ln(1 + r * t); multiply by P0 gives growth magnitude,
        # then add P0 so that at t=0 → population == P0.
        population = P0 + P0 * np.log1p(r * time)
        model_variables["population"] = population

        # housing variables
        model_variables["households"] = model_variables["population"] / parameters["avg_household_size"]
        model_variables["housholds_to_houses_ratio"] = model_variables["households"] / houses
        model_variables["housing_scarcity"] = max(0, (1 - model_variables["housholds_to_houses_ratio"])) #NOTE: Goes from 0 to 1, where 0 means no scarcity and 1 means maximum scarcity
        model_variables["effect_of_housing_scarcity_on_cost"] = self.u.normalized_exp_growth(model_variables["housing_scarcity"], funct_params["scarcity_sensitivity"]) #NOTE: Goes from 0 to 1
        model_variables["cost_of_housing"] = (1 + model_variables["effect_of_housing_scarcity_on_cost"]) * parameters["avg_housing_cost"] #NOTE: Model output, right now it cannot go below the average housing cost, but it can go above it.

        # financing variables
        model_variables["effect_of_financing_on_construction_rate"] = self.u.saturating_response(policies["financial_availability"], funct_params["K_fin"]) #NOTE: Goes from 0 to 1

        # taxes variables
        model_variables["effect_of_taxes_on_construction_rate"] = self.u.normalized_exp_growth(policies["tax_rate"], funct_params["elasticity_tax"]) # NOTE: Goes from 0 to 1# TODO: needs delay
        
        # funding variables
        model_variables["compliance_rate"] = self.u.logistic(policies["engagement_with_stakeholders"], funct_params["k_eng"], funct_params["mid_eng"]) #NOTE: Goes from 0 to 1
        model_variables["public_funding"] = model_variables["compliance_rate"] * policies["tax_rate"] * houses * parameters["property_tax"]
        model_variables["funding_for_services"] = model_variables["public_funding"] * (1 - policies["fraction_of_funding_for_transportation"])
        model_variables["funding_for_transportation"] = model_variables["public_funding"] * policies["fraction_of_funding_for_transportation"]

        # transportation investment variables
        model_variables["private_transportation_investment"] = model_variables["funding_for_transportation"] * (1 - policies["fraction_of_investment_in_public_transportation"])
        model_variables["public_transportation_investment"] = model_variables["funding_for_transportation"] * policies["fraction_of_investment_in_public_transportation"]

        # land use variables
        model_variables["density_index"] = (model_variables["public_transportation_investment"] * policies["zoning_and_regulation"]) / model_variables["private_transportation_investment"] #TODO: Should this index be from 0 to 1?
        model_variables["time_in_traffic"] = 1.0 / model_variables["density_index"] #NOTE: This is a model output #TODO: Should we include avg_time_in_traffic as a parameter that multiplies the density index?
        model_variables["land_per_house"] = parameters["avg_land_per_house"] / model_variables["density_index"]
        model_variables["total_land_used_for_housing"] = model_variables["land_per_house"] * houses
        model_variables["fraction_of_total_occupied_land"] = model_variables["total_land_used_for_housing"] / parameters["total_land_area"] #NOTE: Goes from 0 to 1
        model_variables["available_land_for_housing"] = 1 - model_variables["fraction_of_total_occupied_land"] #NOTE: Goes from 0 to 1
        model_variables["city_sprawl"] = model_variables["fraction_of_total_occupied_land"] #NOTE: This is a model output. Goes from 0 to 1

        # services investment variables 
        model_variables["services_demand"] = model_variables["fraction_of_total_occupied_land"] #NOTE: Goes from 0 to 1
        model_variables["services_supply"] = self.u.saturating_response(model_variables["funding_for_services"], funct_params['K_serv']) #NOTE: Goes from 0 to 1
        model_variables["access_to_services"] = model_variables["services_supply"] / model_variables["services_demand"] #NOTE: This is a model output

        # construction variables
        model_variables["effect_of_private_investment_on_base_construction_rate"] = self.u.saturating_response(parameters["private_investment"], funct_params["K_inv"]) #NOTE: Goes from 0 to 1
        model_variables["construction_rate_of_houses"] = (model_variables["effect_of_private_investment_on_base_construction_rate"] * parameters["base_construction_rate"] * model_variables["effect_of_financing_on_construction_rate"]) / model_variables["effect_of_taxes_on_construction_rate"] #TODO: effect of private investment needs delay. #NOTE: Goes from 0 to 1
        model_variables["construction_of_houses"] = houses * model_variables["housing_scarcity"] * model_variables["construction_rate_of_houses"] * model_variables["available_land_for_housing"]

        # Housing stock flows
        model_variables["housing_stock_increase"] = model_variables["construction_of_houses"] #TODO: We have to add a delay effect here, the construction of houses takes time to be reflected in the housing stock
        model_variables["housing_stock_decrease"] = parameters["housing_demolition_rate"] * houses

        return model_variables
    
    
    def calculate_stock_derivatives(self, model_variables: dict) -> float:
        
        # Calculate derivatives based on the model variables
        housesD = model_variables["housing_stock_increase"] - model_variables["housing_stock_decrease"]


        return housesD
    
    def run_step(self, houses, t):
        """
        Executes a single simulation step for the housing model.
        Args:
            houses (dict or custom object): The current state of the housing stock or model variables.
            t (int or float): The current time step or simulation time.
        Returns:
            tuple: A tuple containing:
                - housesD: The computed derivatives or changes in the housing stock.
                - model_variables: The calculated model variables for this time step.
        """
       
        model_variables = self.calculate_model_variables(houses, t)
        housesD = self.calculate_stock_derivatives(model_variables)

        return housesD, model_variables



