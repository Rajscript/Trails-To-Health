import pandas as pd
import numpy as np
from geopy.geocoders import Nominatim
from geopy import distance
from geopy.distance import geodesic
import requests
from TrailRecommedations import TrailRecommendation


class TrailDifficulty:
    def __init__(self, df):
        """
        Initializes a TrailRecommendation object with a list of trail objects.
        
        """
        self.df = df
    def get_lat_long(self, zipcode):
        url = "https://nominatim.openstreetmap.org/search.php"
        params = {"q": zipcode, "format": "jsonv2", "countrycodes": "US"}

        try:
            response = requests.get(url, params=params)
            response_json = response.json()
            if len(response_json) > 0:
                latitude = response_json[0]['lat']
                longitude = response_json[0]['lon']
                return latitude, longitude
            else:
                return None, None
        except:
            return None, None
    
    def get_recommendations(self, user_input):

        # Calculate distance between user's zipcode and each trail
        user_lat, user_long = self.get_lat_long(user_input['Zip'])
        print(self.df.head(20))
        # Filter trails by zip code
        self.df['Distance From You(miles)'] = self.df.apply(lambda row: geodesic((user_lat, user_long), (row['latitude'], row['longitude'])).miles, axis=1)
        h=self.df[(self.df['Difficulty_rating_KModes']==user_input['Difficulty']) & (self.df['Length(miles)']>0.3)] # & (self.df['Length(miles)']>0.2)
        h = h.sort_values('Distance From You(miles)')
        #print(h.head(20))
        return h.head(10)

if __name__ == "__main__":
    # load data
    df = pd.read_csv('Trail_Difficulty.csv')
    #print(df)
    difficulty=TrailDifficulty(df)
    user_input={
        'Zip': '13211', 'Difficulty': 'Very Hard – The Leg-Day Loco'
    }
    df_diff=difficulty.get_recommendations(user_input)
    print(df_diff.head(20))