from utils.utils import Utils
import numpy as np

class HousingModel:

    def __init__(self, config_yaml_path: str):
        # 1) Load config & utils
        self.u      = Utils()
        self.config = self.u.load_yaml(config_yaml_path)

        # 2) Read delays (with defaults)
        delays = self.config.get("delays", {})
        self.tax_delay     = delays.get("tax_effect_delay", 2.0)
        self.inv_delay     = delays.get("private_investment_delay", 1.5)
        self.housing_delay = delays.get("housing_stock_delay", 3.0)
        self.sprawl_delay  = delays.get("sprawl_delay", 3.0)

        # 3) Shortcut to sections of config
        sim_p  = self.config["simulation_parameters"]
        params = self.config["model_parameters"]
        pol    = self.config["model_policies"]
        fp     = self.config["response_function_parameters"]

        # 4) Epsilon to avoid divides by zero
        self.eps = 1e-6

        # 5) Initialize delay stocks
        self.tax_effect_stock       = self.u.normalized_exp_growth(pol["tax_rate"], fp["elasticity_tax"])
        self.inv_effect_stock       = self.u.saturating_response(params["private_investment_base"], fp["K_inv"])
        self.housing_increase_stock = 0.0

        # 6) Initial sprawl stock from initial households & avg land per house
        houses0     = sim_p["houses_init"]
        hh0         = params["initial_pop"] / params["avg_household_size"]
        avg_lph0    = params["avg_land_per_house"]
        total_land0 = avg_lph0 * houses0
        hhpkm2_0    = hh0 / max(total_land0, self.eps)
        dense       = fp["dense_city_density"]
        self.sprawl_stock = dense / hhpkm2_0

    def calculate_model_variables(self, houses, time):
        """Compute all the ‘instantaneous’ variables *except* geometry & sprawl."""
        params = self.config["model_parameters"]
        pol    = self.config["model_policies"]
        fp     = self.config["response_function_parameters"]
        mv     = {}

        # Population (logistic)
        P0 = params["initial_pop"]
        r  = fp["pop_growth_rate"]
        K  = fp["pop_carrying_capacity"]
        mv["population"] = K / (1 + ((K - P0) / P0) * np.exp(-r * time))

        # Housing basics
        mv["households"] = mv["population"] / params["avg_household_size"]
        mv["houses_to_households_ratio"] = houses / mv["households"]
        mv["housing_scarcity"] = max(0, 1 - mv["houses_to_households_ratio"])
        mv["housing_slack"]   = max(0, mv["houses_to_households_ratio"] - 1)

        # Housing cost response
        mv["e_scar"] = self.u.normalized_exp_growth(mv["housing_scarcity"], fp["scarcity_sensitivity"])
        mv["e_slack"] = self.u.normalized_exp_growth(mv["housing_slack"],    fp["slack_sensitivity"])
        delta = mv["e_scar"] - mv["e_slack"]
        min_cost = 0.5 * params["avg_housing_cost"]
        mv["housing_cost"] = max(min_cost, (1 + delta) * params["avg_housing_cost"])

        # Financing & private investment
        mv["effect_of_financing_on_construction_rate"] = self.u.saturating_response(
            pol["financial_availability"], fp["K_fin"]
        )
        mv["private_investment"] = params["private_investment_base"] * self.u.power_elasticity(
            mv["housing_scarcity"], fp["inv_scarcity_sensitivity"]
        )

        # Stakeholder compliance → public funding
        mv["compliance_rate"] = self.u.logistic(
            pol["engagement_with_stakeholders"], fp["k_eng"], fp["mid_eng"]
        )
        mv["public_funding"] = (
            mv["compliance_rate"]
            * pol["tax_rate"]
            * houses
            * params["property_tax"]
        )
        mv["funding_for_services"]      = mv["public_funding"] * (1 - pol["fraction_of_funding_for_transportation"])
        mv["funding_for_transportation"] = mv["public_funding"] * pol["fraction_of_funding_for_transportation"]

        # Transportation investments
        mv["public_transportation_investment"]  = mv["funding_for_transportation"] * pol["fraction_of_investment_in_public_transportation"]
        mv["private_transportation_investment"] = mv["funding_for_transportation"] * (1 - pol["fraction_of_investment_in_public_transportation"])

        # Raw transport effects
        mv["effect_pub"]  = self.u.saturating_response(mv["public_transportation_investment"], fp["K_pub"])
        mv["effect_priv"] = 1 - self.u.saturating_response(mv["private_transportation_investment"], fp["K_priv"])

        return mv

    def calculate_stock_derivatives(self, mv):
        """Simple first‐order delay for housing increase."""
        return self.housing_increase_stock - mv["housing_stock_decrease"]

    def run_step(self, houses, time, dt):
        # 1) Instantaneous variables
        mv = self.calculate_model_variables(houses, time)

        # 2) Tax & investment delays
        inst_tax_eff = self.u.normalized_exp_growth(
            self.config["model_policies"]["tax_rate"],
            self.config["response_function_parameters"]["elasticity_tax"]
        )
        inst_inv_eff = self.u.saturating_response(
            mv["private_investment"],
            self.config["response_function_parameters"]["K_inv"]
        )
        self.tax_effect_stock += (inst_tax_eff - self.tax_effect_stock) / self.tax_delay * dt
        self.inv_effect_stock += (inst_inv_eff - self.inv_effect_stock) / self.inv_delay * dt

        mv["effect_of_taxes_on_construction_rate"]            = self.tax_effect_stock
        mv["effect_of_private_investment_on_base_construction_rate"] = self.inv_effect_stock

        # 3) Geometry & sprawl‐stock update
        params = self.config["model_parameters"]
        fp     = self.config["response_function_parameters"]
        pol    = self.config["model_policies"]

        # a) Desired sprawl from current households & avg land
        hh    = mv["households"]
        hhpkm2 = hh / max(params["avg_land_per_house"] * houses, self.eps) #TODO: is there a way that this is caluclated with land_per_house instead?
        desired_sprawl = fp["dense_city_density"] / max(hhpkm2, self.eps) # The sprawl that our stock should aim for

        # b) Sprawl as a stock
        self.sprawl_stock += (desired_sprawl - self.sprawl_stock) / self.sprawl_delay * dt
        mv["city_sprawl"] = self.sprawl_stock

        # c) Proximity, penalized by sprawl
        mv["base_prox"] = pol["zoning_and_regulation"] * mv["effect_pub"] + (1 - pol["zoning_and_regulation"]) * mv["effect_priv"]
        max_sp    = fp.get("max_expected_sprawl", 50.0)
        norm_sp   = min(self.sprawl_stock / max_sp, 1.0)
        alpha     = fp.get("sprawl_penalty_sensitivity", 0.5)

        inst_prox = max(0.01, mv["base_prox"] * (1 - (alpha * norm_sp)))
        mv["proximity_index"] = inst_prox
        mv["time_in_traffic"] = 1.0 / (inst_prox + self.eps)

        # d) Land‐use metrics from new proximity
        min_lnd, max_lnd = fp["min_land_per_house"], fp["max_land_per_house"]
        mv["land_per_house"] = inst_prox * min_lnd + (1 - inst_prox) * max_lnd
        mv["total_land_used_for_housing"]   = mv["land_per_house"] * houses
        mv["fraction_of_total_occupied_land"] = mv["total_land_used_for_housing"] / params["total_land_area"]
        mv["available_land_for_housing"]    = max(0.0, 1 - mv["fraction_of_total_occupied_land"])
        mv["hh_per_km2"] = hh / max(mv["total_land_used_for_housing"], self.eps)

        # e) Services access
        mv["services_demand"] = self.u.saturating_response(mv["hh_per_km2"], fp["K_servd"])
        mv["services_supply"] = self.u.saturating_response(mv["funding_for_services"], fp["K_serv"])
        mv["access_to_services"] = min(mv["services_supply"] / (mv["services_demand"] + self.eps), 1.0)

        # 4) Construction & flows
        mv["construction_rate_of_houses"] = (
            mv["effect_of_private_investment_on_base_construction_rate"]
            * params["base_construction_rate"]
            * mv["effect_of_financing_on_construction_rate"]
        ) / mv["effect_of_taxes_on_construction_rate"]

        mv["construction_of_houses"] = (
            houses
            * mv["housing_scarcity"]
            * mv["construction_rate_of_houses"]
            * mv["available_land_for_housing"]
        )

        # 5) Housing-increase delay
        self.housing_increase_stock += (
            mv["construction_of_houses"] - self.housing_increase_stock
        ) / self.housing_delay * dt
        mv["housing_stock_increase"] = self.housing_increase_stock

        # 6) Demolition & derivative
        mv["housing_stock_decrease"] = params["housing_demolition_rate"] * houses
        housesD = self.calculate_stock_derivatives(mv)

        return housesD, mv
