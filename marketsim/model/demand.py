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

class EvolvingDemand():
    def __init__(self, probability=0.1):
        self.max = market_config['MAX_DEMAND']
        self.demand = int(self.max / 2.0)
        self.probability = probability
    
    def next(self): 
        if(random.random() < self.probability):
            # If its already max, can only go down.
            if self.demand >= self.max:
                self.demand = self.max - 1
            elif self.demand == 0: #If minimum can only go up.
                self.demand = min(1, self.max)
            else:
                # With 50% probability, move up or down
                if(random.random() < 0.5):
                    self.demand  = self.demand - 1
                else:
                    self.demand = self.demand + 1
        return self.demand

class FixedDemand():
    def __init__(self):
        self.max = market_config['MAX_DEMAND']
    
    def next(self): 
        return int(self.max / 2.0)