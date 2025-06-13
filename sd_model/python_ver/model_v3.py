from utils.utils import Utils
import numpy as np

class HousingModel:

    def __init__(self, config_yaml_path: str):
        # Initialize utils and load config
        self.u = Utils()
        self.config = self.u.load_yaml(config_yaml_path)

        # Read delay constants (time units)
        delays = self.config.get("delays", {})
        self.tax_delay = delays.get("tax_effect_delay", 1.0)
        self.inv_delay = delays.get("private_investment_delay", 1.0)
        self.housing_delay = delays.get("housing_stock_delay", 1.0)

        # Initialize delay‐state stocks with their instantaneous values
        params   = self.config["model_parameters"]
        policies = self.config["model_policies"]
        fp       = self.config["response_function_parameters"]

        # Instantaneous at t=0
        self.tax_effect_stock = self.u.normalized_exp_growth(
            policies["tax_rate"],
            fp["elasticity_tax"]
        )
        self.inv_effect_stock = self.u.saturating_response(
            params["private_investment"],
            fp["K_inv"]
        )
        # Start housing increase delay stock at zero
        self.housing_increase_stock = 0.0

    def calculate_model_variables(self, houses, time):
        params   = self.config["model_parameters"]
        policies = self.config["model_policies"]
        fp       = self.config["response_function_parameters"]
        mv = {}

        # Population (logistic growth)
        P0 = params["initial_pop"]
        r  = fp["pop_growth_rate"]
        K  = fp["pop_carrying_capacity"]
        mv["population"] = K / (1 + ((K - P0)/P0) * np.exp(-r * time))

        # Housing basics
        mv["households"] = mv["population"] / params["avg_household_size"]
        mv["houses_to_households_ratio"] = houses / mv["households"]
        mv["housing_scarcity"] = max(0, 1 - mv["houses_to_households_ratio"])
        mv["housing_slack"]   = max(0, mv["houses_to_households_ratio"] - 1)

        # Housing cost
        e_scar = self.u.normalized_exp_growth(
            mv["housing_scarcity"], fp["scarcity_sensitivity"]
        )
        e_slack = self.u.normalized_exp_growth(
            mv["housing_slack"], fp["slack_sensitivity"]
        )
        delta = e_scar - e_slack
        min_cost = 0.5 * params["avg_housing_cost"]
        mv["cost_of_housing"] = max(
            min_cost,
            (1 + delta) * params["avg_housing_cost"]
        )

        # Financing & funding
        mv["effect_of_financing_on_construction_rate"] = self.u.saturating_response(
            policies["financial_availability"], fp["K_fin"]
        )
        mv["compliance_rate"] = self.u.logistic(
            policies["engagement_with_stakeholders"], fp["k_eng"], fp["mid_eng"]
        )
        mv["public_funding"]      = mv["compliance_rate"] * policies["tax_rate"] * houses * params["property_tax"]
        mv["funding_for_services"]      = mv["public_funding"] * (1 - policies["fraction_of_funding_for_transportation"])
        mv["funding_for_transportation"] = mv["public_funding"] * policies["fraction_of_funding_for_transportation"]

        # Transportation investments
        mv["private_transportation_investment"] = mv["funding_for_transportation"] * (1 - policies["fraction_of_investment_in_public_transportation"])
        mv["public_transportation_investment"]  = mv["funding_for_transportation"] * policies["fraction_of_investment_in_public_transportation"]

        # Land use & other vars (unchanged)
        mv["density_index"] = (
            mv["public_transportation_investment"] * policies["zoning_and_regulation"]
        ) / mv["private_transportation_investment"] #TODO: Should this index be from 0 to 1? Check behavior of this variable
        mv["time_in_traffic"] = 1.0 / mv["density_index"] #TODO: Should we include avg_time_in_traffic as a parameter that multiplies the density index?
        mv["land_per_house"] = params["avg_land_per_house"] / mv["density_index"]
        mv["total_land_used_for_housing"] = mv["land_per_house"] * houses
        mv["fraction_of_total_occupied_land"] = mv["total_land_used_for_housing"] / params["total_land_area"]
        mv["available_land_for_housing"] = 1 - mv["fraction_of_total_occupied_land"]
        mv["city_sprawl"] = mv["fraction_of_total_occupied_land"]

        mv["services_demand"] = mv["fraction_of_total_occupied_land"]
        mv["services_supply"] = self.u.saturating_response(
            mv["funding_for_services"], fp['K_serv']
        )
        mv["access_to_services"] = mv["services_supply"] / mv["services_demand"]

        return mv

    def calculate_stock_derivatives(self, mv):
        # Derivative based on delayed housing increase stock
        return self.housing_increase_stock - mv["housing_stock_decrease"]

    def run_step(self, houses, time, dt):
        # 1) Compute instantaneous variables
        mv = self.calculate_model_variables(houses, time)

        # 2) Tax & investment delays
        inst_tax_eff = self.u.normalized_exp_growth(
            self.config["model_policies"]["tax_rate"],
            self.config["response_function_parameters"]["elasticity_tax"]
        )
        inst_inv_eff = self.u.saturating_response(
            self.config["model_parameters"]["private_investment"],
            self.config["response_function_parameters"]["K_inv"]
        )
        self.tax_effect_stock += (inst_tax_eff - self.tax_effect_stock) / self.tax_delay * dt
        self.inv_effect_stock += (inst_inv_eff - self.inv_effect_stock) / self.inv_delay * dt
        mv["effect_of_taxes_on_construction_rate"]           = self.tax_effect_stock
        mv["effect_of_private_investment_on_base_construction_rate"] = self.inv_effect_stock

        # 3) Construction & housing flows
        mv["construction_rate_of_houses"] = (
            mv["effect_of_private_investment_on_base_construction_rate"]
            * self.config["model_parameters"]["base_construction_rate"]
            * mv["effect_of_financing_on_construction_rate"]
        ) / mv["effect_of_taxes_on_construction_rate"]
        mv["construction_of_houses"] = (
            houses * mv["housing_scarcity"]
            * mv["construction_rate_of_houses"]
            * mv["available_land_for_housing"]
        )

        # 4) Housing increase delay stock: first-order delay
        self.housing_increase_stock += (mv["construction_of_houses"] - self.housing_increase_stock) / self.housing_delay * dt
        mv["housing_stock_increase"] = self.housing_increase_stock

        # 5) Demolition
        mv["housing_stock_decrease"] = self.config["model_parameters"]["housing_demolition_rate"] * houses

        # 6) Compute derivative
        housesD = self.calculate_stock_derivatives(mv)
        return housesD, mv
