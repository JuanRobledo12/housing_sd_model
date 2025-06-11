from utils.utils import Utils

class ModelVariables:

    def __init__(self, config_yaml_path: str):

        # Initialize an instance of Utils to load the YAML file
        self.utils = Utils()
        self.config_yaml_path = config_yaml_path

    def load_config_file(self) -> dict:
        
        return self.utils.load_yaml(self.config_yaml_path)
    

    def calculate_model_variables(self, houses) -> dict:
        """
        Calculate model variables based on the provided parameters.

        :param parameters: Dictionary containing model parameters.
        :return: Dictionary containing calculated model variables.
        """
        # load config setup from the YAML file
        config = self.load_config_file()
        parameters = config["model_parameters"]
        policies = config["model_policies"]


        # Initialize an empty dictionary to store model variables
        model_variables = {}

        # housing variables
        model_variables["households"] = parameters["population"] / parameters["avg_household_size"]
        model_variables["housing_scarcity"] = model_variables["households"] / houses #NOTE: houses is a stock. If it's > 1 we don't have enough houses for all households
        model_variables["effect_of_housing_scarcity_on_cost"] = model_variables["house_scarcity"] #TODO: This should be like an elasticity function or activation function that we need to define
        model_variables["cost_of_housing"] = model_variables["effect_of_housing_scarcity_on_cost"] #NOTE: Model output

        # financing variables
        model_variables["effect_of_financing_on_construction_rate"] = policies["financing_availability"] #TODO: This should be like an elasticity function or activation function that we need to define      

        # taxes variables
        model_variables["effect_of_taxes_on_construction_rate"] = policies["tax_rate"] #TODO: This should be like an elasticity function or activation function that we need to define. In addition, the tax_rate should have a delayed effect on the effect of taxes on construction rate
        
        # funding variables
        model_variables["compliance_rate"] = policies["engagement_with_stakeholders"] #TODO: This should be a multiplicative effect or an activation function that we need to define
        model_variables["public_funding"] = model_variables["compliance_rate"] * policies["tax_rate"] * houses #TODO: Make sure this calculation is correct
        model_variables["funding_for_services"] = model_variables["public_funding"] * (1 - policies["fraction_of_funding_for_transportation"]) #TODO: Make sure this calculation is correct
        model_variables["funding_for_transportation"] = model_variables["public_funding"] * policies["fraction_of_funding_for_transportation"] #TODO: Make sure this calculation is correct

        # transportation investment variables
        model_variables["private_transportation_investment"] = model_variables["funding_for_transportation"] * (1 - policies["fraction_of_investment_in_public_transportation"]) #TODO: Make sure this calculation is correct
        model_variables["public_transportation_investment"] = model_variables["funding_for_transportation"] * policies["fraction_of_investment_in_public_transportation"] #TODO: Make sure this calculation is correct

        # land use variables
        model_variables["density_index"] = (model_variables["public_transportation_investment"] / model_variables["private_transportation_investment"]) * policies["zoning_and_regulation"] #TODO: Make sure this calculation is correct the idea is that public transport increases density and private transportation decreases density and the zoning and regulation policies can help to increase density or not
        model_variables["avg_time_in_traffic"] = model_variables["density_index"] #TODO: This needs more work, the idea is that the higher the density index the more proximate the households are to services and transportation, thus less time in traffic #NOTE: This is a model output
        model_variables["land_per_house"] = parameters["gdp_per_capita"] / model_variables["density_index"] #TODO: This needs more work, the variable should reflect the land used per house, the higher the density index the less land is used per house and the higher the gdp per capita the more land is used per house. Maybe we need a better name for this variable
        model_variables["total_land_used_for_housing"] = model_variables["land_per_house"] * houses #TODO: Make sure this calculation is correct
        model_variables["fraction_of_total_occupied_land"] = model_variables["total_land_used_for_housing"] / parameters["total_land_area"]
        model_variables["available_land_for_housing"] = 1 - model_variables["fraction_of_total_occupied_land"]
        model_variables["city_sprawl"] = model_variables["fraction_of_total_occupied_land"] #NOTE: This is a model output, I am not sure if this needs an additional calculation, or if it make sense

        # services investment variables
        model_variables["services_demand"] = model_variables["fraction_of_total_occupied_land"] #TODO: This needs more work, the idea is that the higher the fraction of total occupied land the more services are needed I am not sure if we need an additional parameter or calculation here
        model_variables["services_supply"] = model_variables["funding_for_services"] #TODO: This needs more work, it should reflect the services supply based on the funding maybe we need a parameter
        model_variables["access_to_services"] = model_variables["services_supply"] / model_variables["services_demand"] #NOTE: This is a model output and if this is > 1 we have enough services for all households

        # construction variables
        model_variables["effect_of_private_investment_on_base_construction_rate"] = parameters["private_investment"] #TODO: This should be like an elasticity function or activation function that we need to define.
        model_variables["construction_rate_of_houses"] = model_variables["effect_of_private_investment_on_base_construction_rate"] * parameters["base_construction_rate"] * model_variables["effect_of_financing_on_construction_rate"] * model_variables["effect_of_taxes_on_construction_rate"] # TODO: Make sure this calculation is correct, the effect of taxes should have a negative effect on construction rate. In addition the effect of private investment should have a delayed effect on the construction rate
        model_variables["construction_of_houses"] = houses * model_variables["housing_scarcity"] * model_variables["construction_rate_of_houses"] * model_variables["available_land_for_housing"] #TODO: Make sure this calculation is correct


        # Housing stock flows
        model_variables["housing_stock_increase"] = model_variables["construction_of_houses"] #TODO: We have to add a delay effect here, the construction of houses takes time to be reflected in the housing stock
        model_variables["housing_stock_decrease"] = parameters["housing_demolition_rate"] * houses

        return model_variables
    
    
    def calculate_stock_derivatives(self, model_variables: dict) -> float:
        
        
        # Calculate derivatives based on the model variables
        housesD = model_variables["housing_stock_increase"] - model_variables["housing_stock_decrease"]


        return housesD



