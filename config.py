import yaml

class Config:
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        with open('config.yaml', 'r') as file:
            self.config = yaml.safe_load(file)

