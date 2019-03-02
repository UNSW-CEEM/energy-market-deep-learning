import csv

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
