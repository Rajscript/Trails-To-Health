
import streamlit as st
from streamlit import components
import pandas as pd
from TrailRecommedations import TrailRecommendation
from TrailDifficulty import TrailDifficulty
import re
import os
import streamlit.components.v1 as components
import base64


app_root = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(app_root, 'Finalized_Trail_paths.csv')

df = pd.read_csv(csv_path)
trails = TrailRecommendation(df)
trails.preprocess_data()

@st.cache_data
def get_img_as_base64(file):
    with open(file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

@st.cache
def get_recommendations(user_input):
    recommendations = trails.get_recommendations(user_input)
    recommendations['Site Name'] = recommendations.apply(lambda row: '<a href="{}">{}</a>'.format(row['website'], row['site_name']), axis=1)
    selected_rec = recommendations[['Site Name', 'Name', 'Length(miles)', 'Elevation Gain(feet)', 'Distance From You(miles)']]
    return selected_rec

def home_page():
    with open("App/static/map.html", "r") as file:
        html_content = file.read()
    st.components.v1.html(html_content, height=800)

def recommendation_page():
    zip_pattern = r'^\d{5}$'
    zip_code = st.text_input("Enter your zip code:")
    exploration_mode = st.selectbox("Exploration mode", ['Walk', 'Bike', 'Horse riding', 'Snowmobile', 'Accessible'])
    elevation_gain = st.number_input("Elevation gain (m)", value=0, min_value=0)
    trail_length = st.number_input("Trail length (miles)", value=0, min_value=0)
    experience = st.selectbox("Experience level", ['Beginner', 'Moderate', 'Experienced'])
    distance = st.selectbox("Filter by distance", ['All', 'Within 10 miles', 'Within 50 miles', 'Within 100 miles'])

    if st.button("Submit"):
        # Validate user input
        if not re.match(zip_pattern, zip_code):
            st.error('Invalid zip code')
            return

        if not isinstance(trail_length, int) or trail_length <= 0:
            st.error('Trail length should be a positive integer')
            return

        if not isinstance(elevation_gain, int) or elevation_gain <= 0:
            st.error('Elevation gain should be a positive integer')
            return
        # Create user input dictionary
        user_input = {
            'Zip': zip_code,
            'Foot': 'Y' if exploration_mode == 'Walk' else 'N',
            'Horse': 'Y' if exploration_mode == 'Horse riding' else 'N',
            'Bike': 'Y' if exploration_mode == 'Bike' else 'N',
            'Snowmb': 'Y' if exploration_mode == 'Snowmobile' else 'N',
            'Accessible': 'Y' if exploration_mode == 'Accessible' else 'N',
            'Trail_Leng': trail_length,
            'Elevation_Gain': elevation_gain,
            'type_factor': experience.lower(),
            'radius': 0 if distance == 'All' else int(distance.split()[1])
        }

        # Get recommendations
        recommendations = trails.get_recommendations(user_input)
        recommendations['Site Name'] = recommendations.apply(lambda row: f'<a href="{row["website"]}">{row["site_name"]}</a>', axis=1)
        selected_rec = recommendations[['Site Name', 'Name', 'Length(miles)', 'Elevation Gain(feet)', 'Distance From You(miles)']]

        if selected_rec.empty:
            st.warning("Sorry! No matches were found.")
        else:
            #st.table(selected_rec)
            # Render the recommendations using the recommend.html template
            #with open("templates/recommend.html", "r") as file:
                #html_content = file.read()
            #recommendations_html = html_content.replace("{{ recommendations|safe }}", selected_rec.to_html(index=False, render_links=True, escape=False))
            #st.components.v1.html(recommendations_html, height=3000)
            recommendations_table = selected_rec.to_html(index=False, render_links=True, escape=False)

            custom_style = '<style>.dataframe { max-height: 1000px; overflow-y: auto; background-color: white; padding: 10px;}</style>'
            st.markdown(custom_style, unsafe_allow_html=True)
            with st.container():
                 st.markdown(recommendations_table, unsafe_allow_html=True)



def difficulty_page():
    zip_code = st.text_input("Enter your zip code:")
    difficulty_level = st.selectbox("Difficulty level", ['Easy', 'Medium', 'Hard'])

    if st.button("Submit"):
        # Read the difficulty data
        df_difficulty = pd.read_csv('App/Trail_Difficulty.csv')

        # Create user input dictionary
        user_input = {
            'Zip': zip_code,
            'Difficulty': difficulty_level
        }

        # Get recommendations
        diff = TrailDifficulty(df_difficulty)
        df_reco = diff.get_recommendations(user_input)
        df_reco['Site Name'] = df_reco.apply(lambda row: f'<a href="{row["website"]}">{row["site_name"]}</a>', axis=1)
        df_reco['Elevation Gain(feet)'] = df_reco['Elevation_Gain'] / 3.28
        df_reco = df_reco[['Distance From You(miles)', 'Site Name', 'Name', 'Length(miles)', 'Elevation Gain(feet)', 'type_factor']]
        recommendations_table = df_reco.to_html(index=False, render_links=True, escape=False, classes='table', header=True, border=0,
                                               table_id='recommendations-table')
        custom_style = '<style>.dataframe { max-height: 1000px; overflow-y: auto; background-color: white; padding: 10px;}</style>'

        st.markdown(custom_style, unsafe_allow_html=True)

        with st.container():
                 st.markdown(recommendations_table, unsafe_allow_html=True)


def run_streamlit_app():
    img = get_img_as_base64("App/static/image.jpg")
    page_bg_img = f"""
    <style>
    [data-testid="stAppViewContainer"] {{
    background-image: url("https://images.unsplash.com/photo-1508615070457-7baeba4003ab?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1740&q=80");
    background-size: 180%;
    background-position: top left;
    background-repeat: no-repeat;
    background-attachment: local;
    }}

    [data-testid="stSidebar"] > div:first-child {{
    background-image: url("data:image/png;base64,{img}");
    background-position: center; 
    background-repeat: no-repeat;
    background-attachment: local;
    }}

    [data-testid="stHeader"] {{
    background: rgba(0,0,0,0);
    }}
    </style>
    """

    st.markdown(page_bg_img, unsafe_allow_html=True)
    #st.title('limegreen[_Trails To Health_]')
    st.markdown('<h1 style="color: forestgreen;">Trails To Health</h1>', unsafe_allow_html=True)
    page = st.sidebar.radio("Navigation", ["Home", "Recommendation", "Difficulty"],
                            key="navigation")

    if page == "Home":
        home_page()
    elif page == "Recommendation":
        recommendation_page()
    elif page == "Difficulty":
        difficulty_page()

run_streamlit_app()