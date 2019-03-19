
# import dependency_injector.containers as containers
import dependency_injector.providers as providers
import requests
import json

POST_URL='https://deeplearninglog.herokuapp.com/api/simdata'
# Need to make this threadsafe for sure. 
class Log():
    def __init__(self):
        print("Logbook created.")
        self.data = {
            'label':None,
            'hyperparameters':{},
            'metadata':{},
            
            
            
            'timeseries':{
                'epoch_reward':{
                    'label':'Epoch Reward',
                    'data':[]
                },
                'demand':{
                    'label':'Demand',
                    'data':[]
                },
                'price':{
                    'label':'Price',
                    'data':[]
                }
            },
            'bids':{},
            
            'bidstacks': {
                # 0 :{
                #     'nyngan': {
                #         'meta': {
                #             'label': 'nyngan',
                #         },
                #         'bands': {
                #             1: {
                #             'price': 30,
                #             'volume': 10
                #             },
                #             2: {
                #             'price': 2,
                #             'volume': 5
                #             }
                #         }
                #     }
                # },
                
            }
            
        }
        
    
    def get_data(self):
        return self.data
    
    def set_data(self, data):
        self.data = data
    
    def set_label(self, label):
        print("Setting label", label)
        self.data['label'] = label

    def record_hyperparameter(self, label, value):
        print("Recording Hyperparameter", label, value)
        self.data['hyperparameters'][label] = value
    
    def record_model_json(sellf, json):
        self.data['model_json'] = json
        
    def record_metadata(self, label, value):
        self.data['metadata'][label] = value

    def record_epoch_reward(self, reward):
        self.data['timeseries']['epoch_reward']['data'].append(reward)
    
    def record_bid(self, participant_label, price, volume, step_no):
        step_no = int(step_no)
        # Initialise if not in the dict. 
        self.data['bidstacks'][step_no] = {} if not step_no in self.data['bidstacks'] else self.data['bidstacks'][step_no]
        self.data['bidstacks'][step_no][participant_label] = { 'bands':[], 'meta':{'label':participant_label}} if not participant_label in  self.data['bidstacks'][step_no] else self.data['bidstacks'][step_no][participant_label]
        # Add the actual bid data. 
        self.data['bidstacks'][step_no][participant_label]['bands'].append({'price':price, 'volume':volume})
        
    def record_demand(self, demand):
        self.data['timeseries']['demand']['data'].append(demand)
    
    def record_price(self, price):
        self.data['timeseries']['price']['data'].append(price)

    def submit(self):
        print("Submitting to remote server")
        # try:
        requests.post(POST_URL, data=json.dumps(self.data))
        print("Successfully submitted")
        # except:
        #     print("Logbook submission failed.")
        
# Need to use a dependency injector version so that in all imports/calls, we get the same object.

logbook = providers.Singleton(Log)


