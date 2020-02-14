
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
            'notes':"",
            
            
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
            # 'demand':{},
            
            'bidstacks': {
                # 0 :{
                #     'nyngan': {
                #         'meta': {
                #             'label': 'nyngan',
                #         },
                #         'bands': []
                #             {
                #             'price': 30,
                #             'volume': 10
                #             },
                #             {
                #             'price': 2,
                #             'volume': 5
                #             }
                #         ]
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
    
    def record_model_json(self, json):
        self.data['model_json'] = json

    def record_metadata(self, label, value):
        self.data['metadata'][label] = value

    def record_epoch_reward(self, reward):
        self.data['timeseries']['epoch_reward']['data'].append(reward)
    
    def record_notes(self, notes):
        self.data['notes'] += notes+"\n"
    
    def record_bid(self, participant_label, price, volume,  step_no):
        step_no = int(step_no)
        # Initialise if not in the dict. 
        self.data['bidstacks'][step_no] = {} if not step_no in self.data['bidstacks'] else self.data['bidstacks'][step_no]
        self.data['bidstacks'][step_no][participant_label] = { 'bands':[], 'meta':{'label':participant_label}} if not participant_label in  self.data['bidstacks'][step_no] else self.data['bidstacks'][step_no][participant_label]
        # Add the actual bid data. 
        self.data['bidstacks'][step_no][participant_label]['bands'].append({'price':price, 'volume':volume})
        
    def record_demand(self, demand, step_no):
        self.data['timeseries']['demand']['data'].append([step_no, demand]) #record for basic chart
    
    def record_price(self, price, step_no):
        self.data['timeseries']['price']['data'].append([step_no,price])

    def submit(self):
        """
            Attempts to send the logbook data to the logbook server.
            For anything more than a test, it is worth calling trim() before this function.
        """

        print("Submitting to remote server")
        # try:
        requests.post(POST_URL, data=json.dumps(self.data))
        print("Successfully submitted")
        # except:
        #     print("Logbook submission failed.")
    
    def get_num_unique_bids(self, previous_steps):
        all_step_nums = sorted([x for x in self.data['bidstacks']])
        relevant_step_nums = all_step_nums[-previous_steps:]
        
        previously_seen_bids = []
        for i in relevant_step_nums:
            bid_string = ""
            for participant_label in self.data['bidstacks'][i]:
                temp_bid_list = []
                
                for b in self.data['bidstacks'][i][participant_label]['bands']:
                    # print(b, participant_label, self.data['bidstacks'][i]['participant_label']['bands'][b])
                    temp_bid_list.append(b)
                sortedbids = sorted(temp_bid_list, key = lambda bid: (bid['price']))
                for bid in sortedbids:
                    bid_string += str(bid['price'])
                    bid_string += str(bid['volume'])
            if not bid_string in previously_seen_bids:
                previously_seen_bids.append(bid_string)
        
        return len(previously_seen_bids)
    
    def save_json(self, label=""):
        with open('result_'+label+'.json', 'w') as f:
            json.dump(self.data, f)

    def trim(self):
        """
            This function trims the timeseries output of the logbook 
            so that it can be sent via a single http request to the logbook server.
        """
        TRIM_LENGTH = 200
        # Trim the simple timeseries arrays
        for key in self.data['timeseries']:
            self.data['timeseries'][key]['data'] = self.data['timeseries'][key]['data'][-TRIM_LENGTH:]
            
        # Trim the bidstack arrays.
        step_nos = [x for x in self.data['bidstacks']]
        step_nos = step_nos[-TRIM_LENGTH:]
        
        new_bidstacks = {}
        for i in range(len(step_nos)):
            new_bidstacks[step_nos[i]] = self.data['bidstacks'][step_nos[i]]
            
        self.data['bidstacks'] = new_bidstacks
        # Done
        pass
    
        
# Need to use a dependency injector version so that in all imports/calls, we get the same object.

logbook = providers.Singleton(Log)


