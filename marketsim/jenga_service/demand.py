from mongoengine import *
import pendulum
class Demand(Document):
    date_time = DateTimeField()
    demand = FloatField()
    region = StringField()

def get_demand(state, dt):
    dt = pendulum.instance(dt)
    start_date = dt.subtract(minutes=1)
    end_date = dt.add(minutes=1)
    demand_search = Demand.objects(date_time__gte=start_date, date_time__lte=end_date, region=state).order_by('date_time')
    demand_search = [d for d in demand_search]
    if len(demand_search) > 0:
        return demand_search[0].demand
    else:
        print("Demand not found!")
        return 0