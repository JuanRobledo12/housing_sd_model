import yaml

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
