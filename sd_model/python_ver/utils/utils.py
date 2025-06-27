import yaml
import numpy as np

class Utils:
    @staticmethod
    def load_yaml(file_path: str) -> dict:
        """
        Load a YAML file and return its content as a dictionary.
        
        :param file_path: Path to the YAML file.
        :return: Dictionary containing the YAML content.
        """
        with open(file_path, 'r') as file:
            return yaml.safe_load(file)
    
    def power_elasticity(self, x: float, elasticity: float) -> float:
        """A simple power‐law: x**elasticity."""
        return x**elasticity
    
    def normalized_power_elasticity(self, x: float, elasticity: float, min_val: float, max_val: float) -> float:
        """Normalized power‐law: (x**elasticity - min_val) / (max_val - min_val)."""
        power_value = x ** elasticity
        normalized_value = (power_value - min_val) / (max_val - min_val)
        return normalized_value

    def saturating_response(self, x: float, half_sat: float) -> float:
        """
        Compute a saturating (Michaelis-Menten type) response.

        This function returns a value between 0 and 1, following the formula:
            response = x / (half_sat + x)

        The `half_sat` parameter determines the input value at which the response reaches half of its maximum (0.5).
        Larger values of `half_sat` cause the response to saturate more slowly.

        :param x: Input value.
        :param half_sat: Half-saturation constant.
        :return: Saturating response between 0 and 1.
        """
        return x/(half_sat + x) if (half_sat + x) > 0 else 0

    def exp_decay(self, x: float, sensitivity: float) -> float:
        """Negative exponential: exp(–sensitivity * x)."""
        return np.exp(-sensitivity * x)
    
    def normalized_exp_growth(self, x: float, sensitivity: float) -> float:
        """Normalized positive exponential: (exp(sensitivity * x) - 1) / (exp(sensitivity) - 1)."""
        exp_value = np.exp(sensitivity * x)
        return (exp_value - 1) / (np.exp(sensitivity) - 1) if (np.exp(sensitivity) - 1) != 0 else 0
    
    def exp_growth(self, x: float, sensitivity: float) -> float:
        """Positive exponential: exp(sensitivity * x)."""
        return np.exp(sensitivity * x)

    def logistic(self, x: float, steepness: float, midpoint: float) -> float:
        """Logistic curve between 0 and 1."""
        return 1 / (1 + np.exp(-steepness*(x - midpoint)))
