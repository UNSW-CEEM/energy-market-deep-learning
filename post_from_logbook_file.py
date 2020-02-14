from marketsim.logbook.logbook import Log
import json
import sys


fname = 'results/result_108.json'
with open(fname) as f:
    data = json.load(f)
    l = Log()
    l.data = data
    l.trim()
    
    for key in l.data:
        print("     ",key, " ---- ", sys.getsizeof(json.dumps(l.data[key])), "bytes")
    l.submit()
