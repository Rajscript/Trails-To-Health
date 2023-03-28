from flask import Flask, render_template, request, flash, redirect, Markup 
from IPython.display import HTML
from flask_table import Table, Col
import pandas as pd
from TrailRecommedations import TrailRecommendation
from TrailDifficulty import TrailDifficulty
import folium
import re

app = Flask(__name__)

df = pd.read_csv('Finalized_Trail_paths.csv')
print(df)
trails = TrailRecommendation(df)
trails.preprocess_data()

class ItemTable(Table):
    name = Col('Unit')
    description = Col('Name')
    price = Col('Shape_Leng')

@app.route('/difficulty', methods=['GET', 'POST'])
def difficulty():
    #If the form is submitted via POST
    if request.method == 'POST':
        zip_code = request.form.get('zip')
        difficulty_level = request.form.get('difficulty').title()
        print(difficulty_level)
        df_difficulty=pd.read_csv('Trail_Difficulty.csv')
        user_input = {
            'Zip': zip_code,
            'Difficulty': difficulty_level
        }
        print(user_input)
        diff=TrailDifficulty(df_difficulty)
        df_reco=diff.get_recommendations(user_input)
        print(df_reco)
        # Create new column to make it clickable using the website column
        df_reco['Site Name'] = df_reco.apply(lambda row: '<a href="{}">{}</a>'.format(row['website'], row['site_name']), axis=1)
        df_reco['Elevation Gain(feet)'] = df_reco['Elevation_Gain']/3.28
        print(df_reco['Elevation_Gain'])
        df_reco=df_reco[['Distance From You(miles)', 'Site Name', 'Name', 'Length(miles)', 'Elevation Gain(feet)' ]]
        # Convert the recommendation dataframe to an HTML table
        recommendations_table = Markup(df_reco.to_html(index=False, render_links=True,
    escape=False))
        print(recommendations_table)
        return render_template('bootstrap.html', table=recommendations_table)
    #If the request is submitted via GET
    return render_template('bootstrap.html')

# Define a route to display the recommendation form
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/recommend', methods=['post'])
def recommend():
    zip_pattern = r'^\d{5}$'
    #Retrieve user input from the form
    try:
       zip_code = request.form['zip']
       #print(zip_code)
       exploration_mode = request.form['transport_mode']
       #print(exploration_mode)
       elevation_gain = request.form['elevation']
       #print(elevation_gain)
       trail_length = request.form['Trail']
       #print(trail_length)
       experience = request.form['experience']
       #print(experience)
       distance = request.form['distance']
       #print(distance)
       # Validate the zip code entered by the user
       if not re.match(zip_pattern, zip_code):
            raise ValueError('Invalid zip code')
       if not trail_length.isnumeric() or int(trail_length) <= 0:
            raise ValueError('Trail length should be a positive integer')
       if not elevation_gain.isnumeric() or int(elevation_gain) <= 0:
            raise ValueError('Elevation gain should be a positive integer')
    except ValueError as e:
    # Return an error message or redirect the user to a new page
        flash(str(e))
        #return redirect('/')
    # Create user input dictionary
    user_input = {
            'Zip': zip_code,
            'Foot': 'Y' if exploration_mode == 'Walk' else 'N',
            'Horse': 'Y' if exploration_mode == 'Horse riding' else 'N',
            'Bike': 'Y' if exploration_mode == 'Bike' else 'N',
            'Snowmb': 'Y' if exploration_mode == 'Snowmobile' else 'N',
            'Accessible': 'Y' if exploration_mode == 'Accessible' else 'N',
            'Trail_Leng': int(trail_length),
            'Elevation_Gain': int(elevation_gain),
            'type_factor': experience.lower(),
            'radius': int(distance)
        }
    print(user_input)
    # Get recommendations
    recommendations = trails.get_recommendations(user_input)
    recommendations['Site Name'] = recommendations.apply(lambda row: '<a href="{}">{}</a>'.format(row['website'], row['site_name']), axis=1)
    #recommendations['Elevation Gain(in feet)'] = recommendations['Elevation_Gain']/3.28
    selected_rec = recommendations[['Site Name', 'Name', 'Length(miles)', 'Elevation Gain(feet)', 'Distance From You(miles)']]
    #print(selected_rec.empty)
    if selected_rec.empty:
       message = "Sorry! No matches were found."
       return render_template('recommend.html', recommendations=message)
    
    # Modify website column to make it clickable
    #selected_rec['website'] = selected_rec.apply(lambda row: '<a href="{}">{}</a>'.format(row['website'], row['website']), axis=1)

    # Convert the recommendation dataframe to an HTML table
    recommendations_table = selected_rec.to_html(index=False, render_links=True,
    escape=False)
    #recommendations=ItemTable(selected_rec.to_dict(orient = 'records'))
    #print(recommendations_table)
    print(recommendations_table)
    return render_template('recommend.html', recommendations=recommendations_table)

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)