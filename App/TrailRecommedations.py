import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import OneHotEncoder
from geopy.geocoders import Nominatim
from geopy import distance
from geopy.distance import geodesic
import requests


class TrailRecommendation:
    """
    A class to recommend trails to users based on their preferences and location.

    Attributes:
        trails (list): a list of trail objects containing information about each trail
        
    Method:
    preprocess_data: a function to encode the trail data
    get_lat_long: a helper function that finds the latitude and longitude based on zip code
    get_recommendation: main function that generates recommedations to the user based on their input and returns top 20 matching trails.
    """
    def __init__(self, df):
        """
        Initializes a TrailRecommendation object with a list of trail objects.
        
        """
        self.df = df
        self.categorical_features = ['Foot', 'Horse', 'Bike', 'Snowmb', 'Accessible']
        self.numerical_features = ['Shape_Leng', 'Elevation_Gain']
        self.type_factor_mapping = {'easy': 0, 'medium': 0.1, 'hard': 0.3}
        
    def preprocess_data(self):
        # One-hot encode categorical features
        for feature in self.categorical_features:
            self.df[feature] = self.df[feature].map({'Y': 1, 'N': 0})
        self.df['type_factor'] = self.df['type_factor'].map({0.0: 'easy', 0.1: 'medium', 0.3: 'hard'})
        #Storing the trail length and elevation length in units of meter and feet respectively
        self.df['Elevation Gain(feet)'] = round(self.df['Elevation_Gain']*3.28)
        self.df['Length(miles)'] = round(self.df['Shape_Leng']*0.000621, 2)
        # Define the bins for the classes
        elevation_bins = [self.df['Elevation_Gain'].min(), 30, 120, self.df['Elevation_Gain'].max()]
        length_bins = [self.df['Shape_Leng'].min(), 1600, 4828, self.df['Shape_Leng'].max()]
        self.df['Shape_Leng'] = pd.cut(self.df['Shape_Leng'], length_bins, labels=['low', 'medium', 'high'], include_lowest=True)
        self.df['Elevation_Gain'] = pd.cut(self.df['Elevation_Gain'], elevation_bins, labels=['low', 'medium', 'high'], include_lowest=True)
        enc = OneHotEncoder()
        encoded_data = enc.fit_transform(self.df[['Shape_Leng', 'Elevation_Gain', 'type_factor']])
        encoded_features = enc.get_feature_names_out(['Shape_Leng', 'Elevation_Gain', 'type_factor'])
        self.encoded_features = encoded_features
        encoded_df = pd.DataFrame(encoded_data.toarray(), columns=encoded_features)
        self.df = pd.concat([self.df, encoded_df], axis=1)
        return self.df
   
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
        # Preprocess user input
        user_df = pd.DataFrame(user_input, index=[0])
        for feature in self.categorical_features:
            user_df[feature] = user_df[feature].map({'Y': 1, 'N': 0})
        # Calculate distance between user's zipcode and each trail
        user_lat, user_long = self.get_lat_long(user_input['Zip'])
        
        user_df['Shape_Leng'] = pd.cut(user_df['Trail_Leng'], bins=[-np.inf, 1, 3, np.inf], labels=['low', 'medium', 'high'])
        user_df['Elevation_Gain'] = pd.cut(user_df['Elevation_Gain'], bins=[-np.inf, 30, 120, np.inf], labels=['low', 'medium', 'high'])
        user_df = pd.get_dummies(user_df, columns=['Shape_Leng', 'Elevation_Gain', 'type_factor'])
        # Add missing type_factor columns
        if 'type_factor_easy' not in user_df:
            user_df['type_factor_easy'] = 0
        if 'type_factor_medium' not in user_df:
            user_df['type_factor_medium'] = 0
        if 'type_factor_hard' not in user_df:
            user_df['type_factor_hard'] = 0
        dist=user_df['radius'].iloc[0]
        
        # Preprocess trail data
        #self.preprocess_data()
        # Filter trails by zip code
        self.df['Distance From You(in miles)'] = self.df.apply(lambda row: geodesic((user_lat, user_long), (row['latitude'], row['longitude'])).miles, axis=1)
        #print(self.df['distance'])
        # Calculate cosine similarity between user input and trails
        X = self.df[self.categorical_features + list(self.encoded_features)]
        y = self.df['Name']
        user_X = user_df[X.columns]
        cosine_sim = cosine_similarity(X, user_X)
        sim_scores = list(enumerate(cosine_sim))
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
        #print(sim_scores)
        trail_indices = [i[0] for i in sim_scores]
        #print(trail_indices)
        h=self.df.loc[trail_indices]
        #print(h)
        # filter the DataFrame by the 'B' column and show the top 20 rows
        if dist != 0:
            filtered_df = h[h['Distance From You(in miles)'] <= dist].head(20)
        else:
            filtered_df = h.head(20)
        print(filtered_df)
        #return y.iloc[trail_indices]
        return filtered_df
    
if __name__ == "__main__":
    # load data
    df = pd.read_csv('Finalized_Trail_paths.csv')
    #print(df)
    
    # create instance of TrailRecommendation class
    trail_recommendation = TrailRecommendation(df)
    
    # preprocess data
    #df_mod=trail_recommendation.preprocess_data()
    #print(df_mod)
    # get user input
    user_input = {'Zip': '13210', 'Trail_Leng': 2.5, 'Elevation_Gain': 80, 'Foot': 'Y', 'Horse': 'N', 'Bike': 'N', 'Snowmb': 'N', 'Accessible': 'N', 'type_factor': 'easy', 'radius': 10}
    
    # get recommendations
    recommendations = trail_recommendation.get_recommendations(user_input)
    
    # print top 20 matching trails
    print(recommendations[['Unit', 'site_name', 'website', 'Name', 'Shape_Leng', 'DR']])
