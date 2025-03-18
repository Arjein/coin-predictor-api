import pandas as pd
import requests


class FearIndexAPI():
    def __init__(self):
        self.endpoint = 'https://api.alternative.me/fng/'
        self.params = {
            'limit':0,
            
        }

    def get_fear_greed_index(self):
        response = requests.get(self.endpoint, params=self.params)
        response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)
        columns= ['value','value_classification','timestamp']
        data = response.json()             
        df = pd.DataFrame(data['data'], columns=columns)
        df['timestamp'] = df['timestamp'].astype('int64') * 1000
        #print(df.head())
        return df

FearIndexAPI().get_fear_greed_index()
    
