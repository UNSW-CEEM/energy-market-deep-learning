import csv
import random
from market_config import params as market_config

class Demand():
    def __init__(self, file_path):
        self.file_path = file_path
        self.demand = []
        self.idx = 0
        with open(file_path) as f:
            reader = csv.DictReader(f)
            for line in reader:
                self.demand.append(line['TOTALDEMAND'])
    
    def next(self):
        demand = float(self.demand[self.idx % len(self.demand)])
        self.idx += 1
        return demand

class RandomDemand():
    def __init__(self):
        self.max = market_config['MAX_DEMAND']
    
    def next(self): 
        return random.random() * float(self.max)

class RandomDiscreteDemand():
    def __init__(self):
        self.max = market_config['MAX_DEMAND']
    
    def next(self): 
        return int(random.random() * float(self.max))