import streamlit as st
from datetime import datetime
from PIL import Image
import pandas as pd
import geopandas as gpd
import pydeck as pdk
import plotly.express as px
from millify import millify
from millify import prettify
import leafmap.colormaps as cm
from leafmap.common import hex_to_rgb
import jenkspy
from datetime import date
import numpy as np

# custo-myze vvvvvvvvvvvvvvvvvvvvvvvv
im = Image.open('content/house2.jpg')
st.set_page_config(
    page_title='Housing Dashboard', 
    layout="wide",
    page_icon=":house:",
    # initial_sidebar_state="collapsed"
    )

# the custom css lives here:
hide_default_format = """
        <style>
            .reportview-container .main footer {visibility: hidden;}    
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            section.main > div:has(~ footer ) {
            padding-bottom: 5px;}
            div.block-container{padding-top:1.5rem;}
            span[data-baseweb="tag"] {
                background-color: #022B3A !important;
                }
            div.css-1r6slb0.e1tzin5v2{
                border: 1px solid; 
                border-radius: 5px;
                color: #022B3A;
                padding: 10px 5px 10px 5px;
                }
            [data-testid="stMetricValue"] {
                color: #FF8966;
                font-size: 30px;
                font-weight:500;
                text-align: center;
                }
            [data-testid="stMetricLabel"] {
                color: #022B3A;
                font-weight:900;
                text-align: center;
                }
        </style>
       """

st.markdown(hide_default_format, unsafe_allow_html=True)

custom_colors_light = ['#ffffff','#ffd8ca','#ffbea8','#ffa487','#FF8966']
custom_colors_dark = ['#ffffff','#a7b2b8','#70828c','#3c5461','#022b3a']
# custo-myze ^^^^^^^^^^^^^^^^^^^^^^^^^

# sidebar variables vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
variable = st.sidebar.radio(
    'Dashboard variable:',(
    'Sales Price', 
    'Sales Price per SF', 
    'Sales Volume', 
    # 'Price Change Over Time'
    ))

# all the quarters available for selection
quarters = st.sidebar.select_slider(
    'Transaction quarter:',
    options=[
    'Q1-18',
    'Q2-18',
    'Q3-18',
    'Q4-18',
    'Q1-19',
    'Q2-19',
    'Q3-19',
    'Q4-19',
    'Q1-20',
    'Q2-20',
    'Q3-20',
    'Q4-20',
    'Q1-21',
    'Q2-21',
    'Q3-21',
    'Q4-21',
    'Q1-22',
    'Q2-22',
    'Q3-22',
    'Q4-22',
    ],
    value=('Q1-20','Q3-21')
)

# how will the quarters be labeled in the title
quarters_title_dict = {
    'Q1-18':'Q1 2018',
    'Q2-18':'Q2 2018',
    'Q3-18':'Q3 2018',
    'Q4-18':'Q4 2018',
    'Q1-19':'Q1 2019',
    'Q2-19':'Q2 2019',
    'Q3-19':'Q3 2019',
    'Q4-19':'Q4 2019',
    'Q1-20':'Q1 2020',
    'Q2-20':'Q2 2020',
    'Q3-20':'Q3 2020',
    'Q4-20':'Q4 2020',
    'Q1-21':'Q1 2021',
    'Q2-21':'Q2 2021',
    'Q3-21':'Q3 2021',
    'Q4-21':'Q4 2021',
    'Q1-22':'Q1 2022',
    'Q2-22':'Q2 2022',
    'Q3-22':'Q3 2022',
    'Q4-22':'Q4 2022',

}

# how the data will be filtered based on the selection of 2 distinct quarters
quarters_filter_dict = {
    'Q1-18':date(2018,1,1),
    'Q2-18':date(2018,4,1),
    'Q3-18':date(2018,7,1),
    'Q4-18':date(2018,10,1),
    'Q1-19':date(2019,1,1),
    'Q2-19':date(2019,4,1),
    'Q3-19':date(2019,7,1),
    'Q4-19':date(2019,10,1),
    'Q1-20':date(2020,1,1),
    'Q2-20':date(2020,4,1),
    'Q3-20':date(2020,7,1),
    'Q4-20':date(2020,10,1),
    'Q1-21':date(2021,1,1),
    'Q2-21':date(2021,4,1),
    'Q3-21':date(2021,7,1),
    'Q4-21':date(2021,10,1),
    'Q1-22':date(2022,1,1),
    'Q2-22':date(2022,4,1),
    'Q3-22':date(2022,7,1),
    'Q4-22':date(2022,10,1),
}

var_dict1 = {
    'Sales Price':'higher median sales prices',
    'Sales Price per SF':'higher median sales price per SF',
    'Sales Volume':'more sales',
    'Price Change Over Time':f'greater change in median sales price per SF from {quarters_title_dict[quarters[0]]} to {quarters_title_dict[quarters[1]]}.',
}

# vintage filter
vintage = st.sidebar.select_slider(
    'Construction vintage:',
    options=['Pre-2000',2000,2005,2010,2015,2020,'Post-2020'],
    value=(2005,2015)
)

# square footage filter
sq_footage = st.sidebar.select_slider(
    'Home size (SF):',
    options=['<1000',1000,2500,5000,'>5000'],
    value=(2500,5000)
)

# sub-geography filter
geography_included = st.sidebar.radio(
    'Geography included:',
    ('Entire county','Sub-geography'),
    index=0
)
sub_geo = ""
if geography_included == 'Sub-geography':
    sub_geo = st.sidebar.multiselect(
        'Select one or more regions:',
        ['Cumming', 'North Forsyth', 'West Forsyth', 'South Forsyth'],
        ['Cumming'])

# sidebar variables ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

# Create dashboard title
if quarters[0] != quarters[1]:
    st.markdown(f"<h2><span style='color:#022B3A'>Forsyth County Housing Trends</span><span style='color:#022B3A'> | </span><span style='color:#FF8966'> {quarters_title_dict[quarters[0]]} - {quarters_title_dict[quarters[1]]}</span></h2>", unsafe_allow_html=True)
else:
    st.markdown(f"<h2><span style='color:#022B3A'>Forsyth County Housing Trends</span><span style='color:#022B3A'> | </span><span style='color:#FF8966'> {quarters_title_dict[quarters[0]]} only</span></h2>", unsafe_allow_html=True)
            
# function to load, join, & filter tabular & geospatial data
@st.cache_data
def load_data():

    # read in tabular data
    df = pd.read_csv('Geocoded_Final_Joined.csv', thousands=',')
    df.rename(columns={
        'Year  Built':'year_blt',
        'Year':'year_sale'
    }, inplace=True)
    df['GEOID'] = df['GEOID'].astype(str)
    df['unique_ID'] = df['Address'] + '-' + df['Sale Date'].astype(str) + '-' + df['price_number'].astype(str)
    df = df[['Address', 'Square Ft', 'year_blt', 'Sale Date', 'year_sale', 'price_number','price_sf','GEOID','Sub_geo','unique_ID']]

    # read in geospatial
    gdf = gpd.read_file('Geography/Forsyth_CTs.geojson')

    # join together the 2, and let not man put asunder
    joined_df = gdf.merge(df, left_on='GEOID', right_on='GEOID')
    joined_df.rename(columns={
        'Sub_geo_x':'Sub_geo',
    }, inplace=True)
    joined_df['Sale Date'] = pd.to_datetime(joined_df['Sale Date']).dt.date
    joined_df = joined_df[['GEOID','geometry','Sale Date','year_sale','Square Ft','year_blt','price_number','price_sf','unique_ID','Sub_geo']]

    # return this
    return joined_df

def filter_data():
    joined_df = load_data()

    # filter by transaction year
    first_date = quarters_filter_dict[quarters[0]]
    second_date = first_date + pd.DateOffset(months=3)
    third_date = quarters_filter_dict[quarters[1]] + pd.DateOffset(months=3)

    if quarters[0] == quarters[1]:
        # this will check if a single quarter is selected from the slider. If so, we want all sales which occured DURING that quarter only
        filtered_df = joined_df[(joined_df['Sale Date'] >= first_date) & (joined_df['Sale Date'] < (second_date))]
    else:
        filtered_df = joined_df[(joined_df['Sale Date'] >= (first_date)) & (joined_df['Sale Date'] < third_date)]

    # filter by construction vintage
    if ((vintage[0] == 'Pre-2000') & (vintage[1] == 'Pre-2000')):
        filtered_df = filtered_df[filtered_df['year_blt'] < 2000]
    elif ((vintage[0] == 'Post-2020') & (vintage[1] == 'Post-2020')):
        filtered_df = filtered_df[filtered_df['year_blt'] > 2020]
    elif ((vintage[0] == 'Pre-2000') & (vintage[1] != 'Post-2020')):
        filtered_df = filtered_df[filtered_df['year_blt'] <= vintage[1]]
    elif ((vintage[0] != 'Pre-2000') & (vintage[1] == 'Post-2020')):
        filtered_df = filtered_df[filtered_df['year_blt'] >= vintage[0]]
    elif ((vintage[0] == 'Pre-2000') & (vintage[1] == 'Post-2020')):
        filtered_df = filtered_df #i.e., don't apply a filter
    else:
        filtered_df = filtered_df[(filtered_df['year_blt'] >= vintage[0]) & (filtered_df['year_blt'] <= vintage[1])]

    # filter by home size (SF)
    if ((sq_footage[0] == '<1000') & (sq_footage[1] == '<1000')):
        filtered_df = filtered_df[filtered_df['Square Ft'] < 1000]
    elif ((sq_footage[0] == '>5000') & (sq_footage[1] == '>5000')):
        filtered_df = filtered_df[filtered_df['Square Ft'] > 5000]
    elif ((sq_footage[0] == '<1000') & (sq_footage[1] != '>5000')):
        filtered_df = filtered_df[filtered_df['Square Ft'] <= sq_footage[1]]
    elif ((sq_footage[0] != '<1000') & (sq_footage[1] == '>5000')):
        filtered_df = filtered_df[filtered_df['Square Ft'] >= sq_footage[0]]
    elif ((sq_footage[0] == '<1000') & (sq_footage[1] == '>5000')):
        filtered_df = filtered_df #i.e., don't apply a filter
    else:
        filtered_df = filtered_df[(filtered_df['Square Ft'] >= sq_footage[0]) & (filtered_df['Square Ft'] <= sq_footage[1])]

    # filter by sub-geography (if applicable)
    if geography_included == 'Sub-geography':
        filtered_df = filtered_df[filtered_df['Sub_geo'].isin(sub_geo)]

    # all we want from this function is the filtered & joined output
    return filtered_df

def map_cumulative_2D():
    df_map = filtered_df.groupby('GEOID').agg({
        'price_number':'median', 
        'price_sf':'median',
        'unique_ID':'count',
        'geometry':pd.Series.mode
        }).reset_index()
    
    df_map = gpd.GeoDataFrame(df_map)
    
    # create the dictionary & columns that will power the map tooltip
    tooltip_label = {
        'Sales Price':'Median sales price: ',
        'Sales Price per SF':'Median price per SF: ',
        'Sales Volume':'Total sales: ',
        }

    df_map['price_number_formatted'] = df_map['price_number'].apply(lambda x: "${:,.0f}".format((x)))
    df_map['price_sf_formatted'] = df_map['price_sf'].apply(lambda x: "${:.2f}".format((x)))
    df_map['unique_ID_formatted'] = df_map['unique_ID'].apply(lambda x: "{:,.0f}".format((x)))

    tooltip_value = {
        'Sales Price':df_map['price_number_formatted'],
        'Sales Price per SF':df_map['price_sf_formatted'] ,
        'Sales Volume':df_map['unique_ID_formatted'] 
        }

    # define columns used for the tooltip
    df_map['tooltip_label'] = tooltip_label[variable]
    df_map['tooltip_value'] = tooltip_value[variable]

    # set choropleth color
    # color_brewer_colors = cm.get_palette('Blues', 5)
    colors_rgb = [hex_to_rgb(c) for c in custom_colors_dark]
    colors_rgb = list(colors_rgb)

    # ignore the first value, which is essentially white
    colors_rgb = colors_rgb[1:]

    var_dict2 = {
        'Sales Price':df_map['price_number'],
        'Sales Price per SF':df_map['price_sf'],
        'Sales Volume':df_map['unique_ID'] 
        }

    # set choropleth column 
    try:
        df_map['choro_color'] = pd.cut(
            var_dict2[variable],
            bins=jenkspy.jenks_breaks(var_dict2[variable], n_classes=4),
            labels=colors_rgb,
            include_lowest=True,
            duplicates='drop'
            )
    except:
        df_map['choro_color'] = pd.cut(
            var_dict2[variable],
            bins=jenkspy.jenks_breaks(var_dict2[variable], n_classes=5),
            labels=colors_rgb,
            include_lowest=True,
            duplicates='drop'
            )

    # create map intitial state
    initial_view_state = pdk.ViewState(
        latitude=34.207054643497315,
        longitude=-84.10535919531371, 
        zoom=9.9, 
        max_zoom=12, 
        min_zoom=8,
        pitch=0,
        bearing=0,
        height=590
    )

    geojson = pdk.Layer(
        "GeoJsonLayer",
        df_map,
        pickable=True,
        autoHighlight=True,
        highlight_color = [255, 255, 255, 80],
        opacity=0.5,
        stroked=True,
        filled=True,
        wireframe=True,
        get_fill_color='choro_color',
        get_line_color=[0, 0, 0, 255],
        line_width_min_pixels=2,
    )
    if variable == 'Sales Volume':
        tooltip = {
            "html": "Census Tract: <b>{GEOID}</b><br>{tooltip_label}<b>{tooltip_value}</b>",
            "style": {"background": "#022B3A", "color": "white", "font-family": "Helvetica"},
            }
    else:
        tooltip = {
            "html": "Census Tract: <b>{GEOID}</b><br>{tooltip_label}<b>{tooltip_value}</b><br>Total Sales: <b>{unique_ID_formatted}</b>",
            "style": {"background": "#022B3A", "color": "white", "font-family": "Helvetica"},
            }

    r = pdk.Deck(
        layers=geojson,
        initial_view_state=initial_view_state,
        map_provider='mapbox',
        map_style='light',
        tooltip=tooltip)


    return r

def map_cumulative_3D():
    df_map = filtered_df.groupby('GEOID').agg({
        'price_number':'median', 
        'price_sf':'median',
        'unique_ID':'count',
        'geometry':pd.Series.mode
        }).reset_index()
    
    df_map = gpd.GeoDataFrame(df_map)
    
    # create the dictionary & columns that will power the map tooltip
    tooltip_label = {
        'Sales Price':'Median sales price: ',
        'Sales Price per SF':'Median price per SF: ',
        'Sales Volume':'Total sales: ',
        }

    df_map['price_number_formatted'] = df_map['price_number'].apply(lambda x: "${:,.0f}".format((x)))
    df_map['price_sf_formatted'] = df_map['price_sf'].apply(lambda x: "${:.2f}".format((x)))
    df_map['unique_ID_formatted'] = df_map['unique_ID'].apply(lambda x: "{:,.0f}".format((x)))

    tooltip_value = {
        'Sales Price':df_map['price_number_formatted'],
        'Sales Price per SF':df_map['price_sf_formatted'] ,
        'Sales Volume':df_map['unique_ID_formatted'] 
        }

    # define columns used for the tooltip
    df_map['tooltip_label'] = tooltip_label[variable]
    df_map['tooltip_value'] = tooltip_value[variable]

    # set choropleth color
    colors = cm.get_palette('Blues', 5)
    colors_rgb = [hex_to_rgb(c) for c in custom_colors_dark]
    colors_rgb = list(colors_rgb)

    # ignore the first value, which is essentially white
    colors_rgb = colors_rgb[1:]

    var_dict2 = {
        'Sales Price':df_map['price_number'],
        'Sales Price per SF':df_map['price_sf'],
        'Sales Volume':df_map['unique_ID'] 
        }
    
    # set choropleth column 
    try:
        df_map['choro_color'] = pd.cut(
            var_dict2[variable],
            bins=jenkspy.jenks_breaks(var_dict2[variable], n_classes=4),
            labels=colors_rgb,
            include_lowest=True,
            duplicates='drop'
            )
    except:
        df_map['choro_color'] = pd.cut(
            var_dict2[variable],
            bins=jenkspy.jenks_breaks(var_dict2[variable], n_classes=5),
            labels=colors_rgb,
            include_lowest=True,
            duplicates='drop'
            )

    # create map intitial state
    initial_view_state = pdk.ViewState(
        latitude=34.192432817081316, 
        longitude= -84.11008422291944,  
        zoom=9.2, 
        max_zoom=12, 
        min_zoom=6,
        pitch=45,
        bearing=0,
        height=590
    )

    geojson = pdk.Layer(
        "GeoJsonLayer",
        df_map,
        pickable=True,
        autoHighlight=True,
        highlight_color = [255, 255, 255, 80],
        opacity=0.5,
        stroked=True,
        filled=True,
        wireframe=True,
        extruded=True,
        get_elevation='unique_ID * 100',
        get_fill_color='choro_color',
        get_line_color='choro_color',
        line_width_min_pixels=2,
    )
    if variable == 'Sales Volume':
        tooltip = {
            "html": "Census Tract: <b>{GEOID}</b><br>{tooltip_label}<b>{tooltip_value}</b>",
            "style": {"background": "#022B3A", "color": "white", "font-family": "Helvetica"},
            }
    else:
        tooltip = {
            "html": "Census Tract: <b>{GEOID}</b><br>{tooltip_label}<b>{tooltip_value}</b><br>Total Sales: <b>{unique_ID_formatted}</b>",
            "style": {"background": "#022B3A", "color": "white", "font-family": "Helvetica"},
            }

    r = pdk.Deck(
        layers=geojson,
        initial_view_state=initial_view_state,
        api_keys = {
            'mapbox':'pk.eyJ1Ijoid3dyaWdodDIxIiwiYSI6ImNsZzU3MjB2YjAwNjIzcm5zMDdtYXJkNXUifQ.FxUvOC7AOzbaCbNQlYONLg'
            },
        map_provider='mapbox',
        map_style='light',
        tooltip=tooltip)

    return r

# def map_delta():
    joined_df = load_data()

    # grab first and last quarters from the range slider
    q1_a = quarters_filter_dict[quarters[0]]
    q1_b = q1_a + pd.DateOffset(months=3)

    q2_a = quarters_filter_dict[quarters[1]]
    q2_b = q2_a + pd.DateOffset(months=3)

    # create first dataframe using the first selected quarter
    df1 = joined_df[(joined_df['Sale Date'] >= q1_a) & (joined_df['Sale Date'] < (q1_b))]
    df2 = joined_df[(joined_df['Sale Date'] >= q2_a) & (joined_df['Sale Date'] < (q2_b))]

    # filter by construction vintage
    if ((vintage[0] == 'Pre-2000') & (vintage[1] == 'Pre-2000')):
        df1 = df1[df1['year_blt'] < 2000]
        df2 = df2[df2['year_blt'] < 2000]
    elif ((vintage[0] == 'Post-2020') & (vintage[1] == 'Post-2020')):
        df1 = df1[df1['year_blt'] > 2020]
        df2 = df2[df2['year_blt'] > 2020]
    elif ((vintage[0] == 'Pre-2000') & (vintage[1] != 'Post-2020')):
        df1 = df1[df1['year_blt'] <= vintage[1]]
        df2 = df2[df2['year_blt'] <= vintage[1]]
    elif ((vintage[0] != 'Pre-2000') & (vintage[1] == 'Post-2020')):
        df1 = df1[df1['year_blt'] >= vintage[0]]
        df2 = df2[df2['year_blt'] >= vintage[0]]
    elif ((vintage[0] == 'Pre-2000') & (vintage[1] == 'Post-2020')):
        df1 = df1 #i.e., don't apply a vintage filter, just grab everything
        df2 = df2
    else:
        df1 = df1[(df1['year_blt'] >= vintage[0]) & (df1['year_blt'] <= vintage[1])]
        df2 = df2[(df2['year_blt'] >= vintage[0]) & (df2['year_blt'] <= vintage[1])]

    # filter by home size (SF)
    if ((sq_footage[0] == '<1000') & (sq_footage[1] == '<1000')):
        df1 = df1[df1['Square Ft'] < 1000]
        df2 = df2[df2['Square Ft'] < 1000]
    elif ((sq_footage[0] == '>5000') & (sq_footage[1] == '>5000')):
        df1 = df1[df1['Square Ft'] > 5000]
        df2 = df2[df2['Square Ft'] > 5000]
    elif ((sq_footage[0] == '<1000') & (sq_footage[1] != '>5000')):
        df1 = df1[df1['Square Ft'] <= sq_footage[1]]
        df2 = df2[df2['Square Ft'] <= sq_footage[1]]
    elif ((sq_footage[0] != '<1000') & (sq_footage[1] == '>5000')):
        df1 = df1[df1['Square Ft'] >= sq_footage[0]]
        df2 = df2[df2['Square Ft'] >= sq_footage[0]]
    elif ((sq_footage[0] == '<1000') & (sq_footage[1] == '>5000')):
        df1 = df1 #i.e., don't apply a SF filter, just grab everything
        df2 = df2
    else:
        df1 = df1[(df1['Square Ft'] >= sq_footage[0]) & (df1['Square Ft'] <= sq_footage[1])]
        df2 = df2[(df2['Square Ft'] >= sq_footage[0]) & (df2['Square Ft'] <= sq_footage[1])]

    # filter by sub-geography (if applicable)
    if geography_included == 'Sub-geography':
        df1 = df1[df1['Sub_geo'].isin(sub_geo)]
        df2 = df2[df2['Sub_geo'].isin(sub_geo)]

    # now run the groupby
    df1_map = df1.groupby('GEOID').agg({
        'price_number':'median', 
        'geometry':pd.Series.mode
        }).reset_index()
    
    df2_map = df2.groupby('GEOID').agg({
        'price_number':'median', 
        'geometry':pd.Series.mode
        }).reset_index()

    df_map_joined = df1_map.merge(df2_map, left_on='GEOID', right_on='GEOID')
    df_map_joined = df_map_joined.rename(columns={
        "price_number_x": "median_price_Q0", 
        "price_number_y": "median_price_Q1",
        "geometry_x": "geometry"
        })

    df_map_joined = df_map_joined[['GEOID', 'geometry', 'median_price_Q0', 'median_price_Q1']]
    df_map_joined['delta'] = (df_map_joined['median_price_Q1'] - df_map_joined['median_price_Q0']) / df_map_joined['median_price_Q0']
    df_map_joined['delta_label'] = df_map_joined['delta'].apply(lambda x: "{:.1f}%".format((x*100)))

    df_map_joined = gpd.GeoDataFrame(df_map_joined)

   # set choropleth color
    colors = cm.get_palette('Blues', 5)
    colors_rgb = [hex_to_rgb(c) for c in colors]
    colors_rgb = list(colors_rgb)

    # ignore the first value, which is essentially white
    colors_rgb = colors_rgb[1:]

    # set choropleth column 
    try:
        df_map_joined['choro_color'] = pd.cut(
            df_map_joined['delta'],
            bins=jenkspy.jenks_breaks(df_map_joined['delta'], n_classes=4),
            labels=colors_rgb,
            include_lowest=True,
            duplicates='drop'
            )
    except:
        df_map_joined['choro_color'] = pd.cut(
            df_map_joined['delta'],
            bins=jenkspy.jenks_breaks(df_map_joined['delta'], n_classes=5),
            labels=colors_rgb,
            include_lowest=True,
            duplicates='drop'
            )

    # create map intitial state
    initial_view_state = pdk.ViewState(
        latitude=34.207054643497315,
        longitude=-84.10535919531371, 
        zoom=9.7, 
        max_zoom=12, 
        min_zoom=8,
        pitch=0,
        bearing=0
    )

    geojson = pdk.Layer(
        "GeoJsonLayer",
        df_map_joined,
        pickable=True,
        autoHighlight=True,
        highlight_color = [255, 255, 255, 80],
        opacity=0.5,
        stroked=True,
        filled=True,
        wireframe=True,
        get_fill_color='choro_color',
        get_line_color=[0, 0, 0, 255],
        line_width_min_pixels=2,
    )

    tooltip = {
        "html": "Census Tract: <b>{GEOID}</b><br>Change in sales price: <b>{delta_label}</b>",
        "style": {"background": "#022B3A", "color": "white", "font-family": "Helvetica"}
        }

    r = pdk.Deck(
        layers=geojson,
        initial_view_state=initial_view_state,
        map_style="light",
        tooltip=tooltip)

    return r

def kpi_median_price():
    price_median = millify(filtered_df['price_number'].median(), precision=0)
    return price_median

def kpi_price_sf():
    price_sf_median = millify(filtered_df['price_sf'].median(), precision=0)
    return price_sf_median

def kpi_median_vintage():
    vintage_median = round(filtered_df['year_blt'].median())
    return vintage_median

def kpi_median_size():
    size_median = prettify(round(filtered_df['Square Ft'].median()))
    return size_median

def kpi_total_sales():
    total_sales = prettify(filtered_df['unique_ID'].count())
    return total_sales

def kpi_Q1_total():
    df = pd.read_csv('Geocoded_Final_Joined.csv', thousands=',')
    df.rename(columns={
        'Year  Built':'year_blt',
        'Year':'year_sale'
    }, inplace=True)
    df['GEOID'] = df['GEOID'].astype(str)
    df['unique_ID'] = df['Address'] + '-' + df['Sale Date'].astype(str) + '-' + df['price_number'].astype(str)
    df = df[['Address', 'Square Ft', 'year_blt', 'Sale Date', 'year_sale', 'price_number','price_sf','GEOID','Sub_geo','unique_ID']]
    df['Sale Date'] = pd.to_datetime(df['Sale Date']).dt.date
    joined_df = df

    # grab first and last quarters from the range slider
    q1_a = quarters_filter_dict[quarters[0]]
    q1_b = q1_a + pd.DateOffset(months=3)

    # create first dataframe using the first selected quarter
    df1 = joined_df[(joined_df['Sale Date'] >= q1_a) & (joined_df['Sale Date'] < (q1_b))]

    # filter by construction vintage
    if ((vintage[0] == 'Pre-2000') & (vintage[1] == 'Pre-2000')):
        df1 = df1[df1['year_blt'] < 2000]
    elif ((vintage[0] == 'Post-2020') & (vintage[1] == 'Post-2020')):
        df1 = df1[df1['year_blt'] > 2020]
    elif ((vintage[0] == 'Pre-2000') & (vintage[1] != 'Post-2020')):
        df1 = df1[df1['year_blt'] <= vintage[1]]
    elif ((vintage[0] != 'Pre-2000') & (vintage[1] == 'Post-2020')):
        df1 = df1[df1['year_blt'] >= vintage[0]]
    elif ((vintage[0] == 'Pre-2000') & (vintage[1] == 'Post-2020')):
        df1 = df1 #i.e., don't apply a vintage filter, just grab everything   
    else:
        df1 = df1[(df1['year_blt'] >= vintage[0]) & (df1['year_blt'] <= vintage[1])]
        
    # filter by home size (SF)
    if ((sq_footage[0] == '<1000') & (sq_footage[1] == '<1000')):
        df1 = df1[df1['Square Ft'] < 1000]  
    elif ((sq_footage[0] == '>5000') & (sq_footage[1] == '>5000')):
        df1 = df1[df1['Square Ft'] > 5000]  
    elif ((sq_footage[0] == '<1000') & (sq_footage[1] != '>5000')):
        df1 = df1[df1['Square Ft'] <= sq_footage[1]]
    elif ((sq_footage[0] != '<1000') & (sq_footage[1] == '>5000')):
        df1 = df1[df1['Square Ft'] >= sq_footage[0]]
    elif ((sq_footage[0] == '<1000') & (sq_footage[1] == '>5000')):
        df1 = df1 #i.e., don't apply a SF filter, just grab everything
    else:
        df1 = df1[(df1['Square Ft'] >= sq_footage[0]) & (df1['Square Ft'] <= sq_footage[1])]

    # filter by sub-geography (if applicable)
    if geography_included == 'Sub-geography':
        df1 = df1[df1['Sub_geo'].isin(sub_geo)]

    # calculate median sales price of the 2 quarters before running the groupby
    df1_median_label = millify(df1['unique_ID'].count(), precision=0)

    return df1_median_label

def kpi_Q2_total():
    df = pd.read_csv('Geocoded_Final_Joined.csv', thousands=',')
    df.rename(columns={
        'Year  Built':'year_blt',
        'Year':'year_sale'
    }, inplace=True)
    df['GEOID'] = df['GEOID'].astype(str)
    df['unique_ID'] = df['Address'] + '-' + df['Sale Date'].astype(str) + '-' + df['price_number'].astype(str)
    df = df[['Address', 'Square Ft', 'year_blt', 'Sale Date', 'year_sale', 'price_number','price_sf','GEOID','Sub_geo','unique_ID']]
    df['Sale Date'] = pd.to_datetime(df['Sale Date']).dt.date
    joined_df = df

    q2_a = quarters_filter_dict[quarters[1]]
    q2_b = q2_a + pd.DateOffset(months=3)

    df2 = joined_df[(joined_df['Sale Date'] >= q2_a) & (joined_df['Sale Date'] < (q2_b))]

    # filter by construction vintage
    if ((vintage[0] == 'Pre-2000') & (vintage[1] == 'Pre-2000')):
        df2 = df2[df2['year_blt'] < 2000]
    elif ((vintage[0] == 'Post-2020') & (vintage[1] == 'Post-2020')):
        df2 = df2[df2['year_blt'] > 2020]
    elif ((vintage[0] == 'Pre-2000') & (vintage[1] != 'Post-2020')):
        df2 = df2[df2['year_blt'] <= vintage[1]]
    elif ((vintage[0] != 'Pre-2000') & (vintage[1] == 'Post-2020')):
        df2 = df2[df2['year_blt'] >= vintage[0]]
    elif ((vintage[0] == 'Pre-2000') & (vintage[1] == 'Post-2020')):
        df2 = df2
    else:
        df2 = df2[(df2['year_blt'] >= vintage[0]) & (df2['year_blt'] <= vintage[1])]

    # filter by home size (SF)
    if ((sq_footage[0] == '<1000') & (sq_footage[1] == '<1000')):
        df2 = df2[df2['Square Ft'] < 1000]
    elif ((sq_footage[0] == '>5000') & (sq_footage[1] == '>5000')):
        df2 = df2[df2['Square Ft'] > 5000]
    elif ((sq_footage[0] == '<1000') & (sq_footage[1] != '>5000')):
        df2 = df2[df2['Square Ft'] <= sq_footage[1]]
    elif ((sq_footage[0] != '<1000') & (sq_footage[1] == '>5000')):
        df2 = df2[df2['Square Ft'] >= sq_footage[0]]
    elif ((sq_footage[0] == '<1000') & (sq_footage[1] == '>5000')):
        df2 = df2
    else:
        df2 = df2[(df2['Square Ft'] >= sq_footage[0]) & (df2['Square Ft'] <= sq_footage[1])]

    # filter by sub-geography (if applicable)
    if geography_included == 'Sub-geography':
        df2 = df2[df2['Sub_geo'].isin(sub_geo)]

    # calculate median sales price of the 2 quarters before running the groupby
    df2_median_label = millify(df2['unique_ID'].count(), precision=0)

    return df2_median_label

def kpi_delta():
    df = pd.read_csv('Geocoded_Final_Joined.csv', thousands=',')
    df.rename(columns={
        'Year  Built':'year_blt',
        'Year':'year_sale'
    }, inplace=True)
    df['GEOID'] = df['GEOID'].astype(str)
    df['unique_ID'] = df['Address'] + '-' + df['Sale Date'].astype(str) + '-' + df['price_number'].astype(str)
    df = df[['Address', 'Square Ft', 'year_blt', 'Sale Date', 'year_sale', 'price_number','price_sf','GEOID','Sub_geo','unique_ID']]
    df['Sale Date'] = pd.to_datetime(df['Sale Date']).dt.date
    joined_df = df

    # grab first and last quarters from the range slider
    q1_a = quarters_filter_dict[quarters[0]]
    q1_b = q1_a + pd.DateOffset(months=3)

    q2_a = quarters_filter_dict[quarters[1]]
    q2_b = q2_a + pd.DateOffset(months=3)

    # create first dataframe using the first selected quarter
    df1 = joined_df[(joined_df['Sale Date'] >= q1_a) & (joined_df['Sale Date'] < (q1_b))]
    df2 = joined_df[(joined_df['Sale Date'] >= q2_a) & (joined_df['Sale Date'] < (q2_b))]

    # filter by construction vintage
    if ((vintage[0] == 'Pre-2000') & (vintage[1] == 'Pre-2000')):
        df1 = df1[df1['year_blt'] < 2000]
        df2 = df2[df2['year_blt'] < 2000]
    elif ((vintage[0] == 'Post-2020') & (vintage[1] == 'Post-2020')):
        df1 = df1[df1['year_blt'] > 2020]
        df2 = df2[df2['year_blt'] > 2020]
    elif ((vintage[0] == 'Pre-2000') & (vintage[1] != 'Post-2020')):
        df1 = df1[df1['year_blt'] <= vintage[1]]
        df2 = df2[df2['year_blt'] <= vintage[1]]
    elif ((vintage[0] != 'Pre-2000') & (vintage[1] == 'Post-2020')):
        df1 = df1[df1['year_blt'] >= vintage[0]]
        df2 = df2[df2['year_blt'] >= vintage[0]]
    elif ((vintage[0] == 'Pre-2000') & (vintage[1] == 'Post-2020')):
        df1 = df1 #i.e., don't apply a vintage filter, just grab everything
        df2 = df2
    else:
        df1 = df1[(df1['year_blt'] >= vintage[0]) & (df1['year_blt'] <= vintage[1])]
        df2 = df2[(df2['year_blt'] >= vintage[0]) & (df2['year_blt'] <= vintage[1])]

    # filter by home size (SF)
    if ((sq_footage[0] == '<1000') & (sq_footage[1] == '<1000')):
        df1 = df1[df1['Square Ft'] < 1000]
        df2 = df2[df2['Square Ft'] < 1000]
    elif ((sq_footage[0] == '>5000') & (sq_footage[1] == '>5000')):
        df1 = df1[df1['Square Ft'] > 5000]
        df2 = df2[df2['Square Ft'] > 5000]
    elif ((sq_footage[0] == '<1000') & (sq_footage[1] != '>5000')):
        df1 = df1[df1['Square Ft'] <= sq_footage[1]]
        df2 = df2[df2['Square Ft'] <= sq_footage[1]]
    elif ((sq_footage[0] != '<1000') & (sq_footage[1] == '>5000')):
        df1 = df1[df1['Square Ft'] >= sq_footage[0]]
        df2 = df2[df2['Square Ft'] >= sq_footage[0]]
    elif ((sq_footage[0] == '<1000') & (sq_footage[1] == '>5000')):
        df1 = df1 #i.e., don't apply a SF filter, just grab everything
        df2 = df2
    else:
        df1 = df1[(df1['Square Ft'] >= sq_footage[0]) & (df1['Square Ft'] <= sq_footage[1])]
        df2 = df2[(df2['Square Ft'] >= sq_footage[0]) & (df2['Square Ft'] <= sq_footage[1])]

    # filter by sub-geography (if applicable)
    if geography_included == 'Sub-geography':
        df1 = df1[df1['Sub_geo'].isin(sub_geo)]
        df2 = df2[df2['Sub_geo'].isin(sub_geo)]

    var_dict_column2 = {
        'Sales Price':'price_number',
        'Sales Price per SF':'price_sf'
    }
    # calculate median sales price of the 2 quarters before running the groupby
    df1_median = df1[var_dict_column2[variable]].median()
    df2_median = df2[var_dict_column2[variable]].median()
    df_median_delta = (df2_median - df1_median) / df1_median
    df_median_label = millify(df_median_delta*100, precision=1)

    return df_median_label

def line_chart():
    # go read the dataaaaa
    df = pd.read_csv('Geocoded_Final_Joined.csv', thousands=',')
    df.rename(columns={
        'Year  Built':'year_blt',
        'Year':'year_sale'
    }, inplace=True)
    df['GEOID'] = df['GEOID'].astype(str)
    df['unique_ID'] = df['Address'] + '-' + df['Sale Date'].astype(str) + '-' + df['price_number'].astype(str)
    df = df[['Address', 'Square Ft', 'year_blt', 'Sale Date', 'year_sale', 'price_number','price_sf','GEOID','Sub_geo','unique_ID']]
    df['Sale Date'] = pd.to_datetime(df['Sale Date']).dt.date
    joined_df = df

    # filter
    if ((vintage[0] == 'Pre-2000') & (vintage[1] == 'Pre-2000')):
        joined_df = joined_df[joined_df['year_blt'] < 2000]
    elif ((vintage[0] == 'Post-2020') & (vintage[1] == 'Post-2020')):
        joined_df = joined_df[joined_df['year_blt'] > 2020]
    elif ((vintage[0] == 'Pre-2000') & (vintage[1] != 'Post-2020')):
        joined_df = joined_df[joined_df['year_blt'] <= vintage[1]]
    elif ((vintage[0] != 'Pre-2000') & (vintage[1] == 'Post-2020')):
        joined_df = joined_df[joined_df['year_blt'] >= vintage[0]]
    elif ((vintage[0] == 'Pre-2000') & (vintage[1] == 'Post-2020')):
        joined_df = joined_df #i.e., don't apply a filter
    else:
        joined_df = joined_df[(joined_df['year_blt'] >= vintage[0]) & (joined_df['year_blt'] <= vintage[1])]

    # filter by home size (SF)
    if ((sq_footage[0] == '<1000') & (sq_footage[1] == '<1000')):
        joined_df = joined_df[joined_df['Square Ft'] < 1000]
    elif ((sq_footage[0] == '>5000') & (sq_footage[1] == '>5000')):
        joined_df = joined_df[joined_df['Square Ft'] > 5000]
    elif ((sq_footage[0] == '<1000') & (sq_footage[1] != '>5000')):
        joined_df = joined_df[joined_df['Square Ft'] <= sq_footage[1]]
    elif ((sq_footage[0] != '<1000') & (sq_footage[1] == '>5000')):
        joined_df = joined_df[joined_df['Square Ft'] >= sq_footage[0]]
    elif ((sq_footage[0] == '<1000') & (sq_footage[1] == '>5000')):
        joined_df = joined_df #i.e., don't apply a filter
    else:
        joined_df = joined_df[(joined_df['Square Ft'] >= sq_footage[0]) & (joined_df['Square Ft'] <= sq_footage[1])]

    # filter by sub-geography (if applicable)
    if geography_included == 'Sub-geography':
        joined_df = joined_df[joined_df['Sub_geo'].isin(sub_geo)]

    # create columns extracting just the month and year from the 'Sale Date' column
    joined_df['year'] = pd.DatetimeIndex(joined_df['Sale Date']).year
    joined_df['month'] = pd.DatetimeIndex(joined_df['Sale Date']).month
    joined_df['year-month'] = joined_df['year'].astype(str) + '-' + joined_df['month'].astype(str)

    # group by 'year-month' to provide a monthly summary of the filtered sales
    df_grouped = joined_df.groupby('year-month').agg({
        'price_number':'median', 
        'price_sf':'median',
        'unique_ID':'count',
        'month':pd.Series.mode,
        'year':pd.Series.mode
        }).reset_index()

    # sort the data so that it's chronological
    df_grouped = df_grouped.sort_values(['year', 'month'])

    # series of dictionaries that will generate the line chart 
    var_dict_column = {
        'Sales Price':df_grouped['price_number'],
        'Sales Price per SF':df_grouped['price_sf'],
        'Sales Volume':df_grouped['unique_ID'],
        'Price Change Over Time':df_grouped['price_number']
    }

    var_dict_title = {
        'Sales Price':'<span style="font-size: 20px;">Median Sales Price per Month</span> <br> <span style="font-size: 14px;">Orange vertical lines show range of selected quarters</span>',
        'Sales Price per SF':'<span style="font-size: 20px;">Median Sales Price / SF per Month</span> <br> <span style="font-size: 14px;">Orange vertical lines show range of selected quarters</span>',
        'Sales Volume':'<span style="font-size: 20px;">Number of Sales per Month</span> <br> <span style="font-size: 14px;">Orange vertical lines show range of selected quarters</span>',
    }

    format_dict = {
        'Sales Price':'$~s',
        'Sales Price per SF':'$.0f',
        'Sales Volume':'',
        'Price Change Over Time':'$~s'
    }

    fig = px.line(
        df_grouped, 
        x="year-month", 
        y=var_dict_column[variable],
        labels={
            'year-month':'Time Period',
            })
    
    # modify the line itself
    fig.update_traces(
        mode="lines",
        line_color='#022B3A',
        hovertemplate=None
        )

    # align title
    if variable == 'Sales Volume':
        fig.update_layout(
            title_text=var_dict_title[variable], 
            title_x=0.05, 
            title_y=0.93,
            title_font_color="#022B3A",
            yaxis = dict(
                title = None,
                tickfont_color = '#022B3A',
                tickfont_size = 14,
                showgrid = False
                ),
            xaxis = dict(
                linecolor = "#FFFFFF",
                linewidth = 1,
                tickfont_color = '#022B3A',
                title = None,
                tickformat = '%b %Y',
                dtick = 'M3'
                ),
            height=530,
            hovermode="x unified")
    else:
        fig.update_layout(
            title_text=var_dict_title[variable], 
            title_x=0.05, 
            title_y=0.93,
            title_font_color="#022B3A",
            yaxis = dict(
                title = None,
                tickformat = format_dict[variable],
                tickfont_color = '#022B3A',
                tickfont_size = 14,
                showgrid = False
                ),
            xaxis = dict(
                linecolor = "#FFFFFF",
                linewidth = 1,
                tickfont_color = '#022B3A',
                title = None,
                tickformat = '%b %Y',
                dtick = 'M3'
                ),
            height=530,
            hovermode="x unified")

    # add shifting vertical lines
    fig.add_vline(x=quarters_filter_dict[quarters[0]], line_width=2, line_dash="dash", line_color="#FF8966")
    if quarters[1] == 'Q4-22':
        fig.add_vline(x=date(2022,12,1), line_width=2, line_dash="dash", line_color="#FF8966")
    else:
        fig.add_vline(x=quarters_filter_dict[quarters[1]] + pd.DateOffset(months=3), line_width=2, line_dash="dash", line_color="#FF8966")

    return fig

# run the function to get and filter data
filtered_df = filter_data()

try:
    KPI_dict = {
        'Sales Price':kpi_median_price(),
        'Sales Price per SF':kpi_price_sf(),
    }
except ValueError as e:
    if str(e).startswith('cannot convert float NaN to integer'):
        st.error('')


try:
    if variable == 'Price Change Over Time':
        col1, col2, col3 = st.columns([2,0.2,2])
        # col1.pydeck_chart(map_delta(), use_container_width=True)
        # col1.markdown("Note: Darker shades of Census tracts represent greater sales volume for the time period selected. Only Census tracts with sales in each quarter selected will show a value on the map. Percent change as calculated subject to rounding error.")
        # with col3:
        #         subcol1, subcol2, subcol3 = st.columns([1, 1, 1])
        #         subcol1.metric(f"{quarters_title_dict[quarters[0]]} Median Price:", f"${kpi_Q1_median()}")
        #         subcol2.metric(f"{quarters_title_dict[quarters[1]]} Median Price:", f"${kpi_Q2_median()}")
        #         subcol3.metric("Percent Change:", f"{kpi_delta()}%")
        # col3.plotly_chart(line_chart(), use_container_width=True, config = {'displayModeBar': False})
    else:
        if variable == 'Sales Volume': #this if / then statement will remove the '3D' option on the radio select if we want to see Total Sales
            col1, col2, col3 = st.columns([2,0.2,2])
            col1.pydeck_chart(map_cumulative_2D(), use_container_width=True)
            col1.markdown("Note: Darker shades of Census tracts represent greater sales volume for the time period selected.")
            with col3:
                subcol1, subcol2, subcol3 = st.columns([1, 1, 1])
                subcol1.metric("Total Home Sales:", kpi_total_sales())
                subcol2.metric(f"Sales in {quarters[0]}:", kpi_Q1_total())
                subcol3.metric(f"Sales in {quarters[1]}:", kpi_Q2_total())
            col3.plotly_chart(line_chart(), use_container_width=True, config = {'displayModeBar': False})
        else:
            col1, col2, col3 = st.columns([2,0.2,2])
            map_view = col2.radio(
                'Map view:',
                ('2D', '3D'),
                index=0
                )
            if map_view == '2D':
                col1.pydeck_chart(map_cumulative_2D(), use_container_width=True)
                col1.markdown(f"Note: Darker shades of Census tracts represent {var_dict1[variable]} for the time period selected.")
            else:
                col1.pydeck_chart(map_cumulative_3D(), use_container_width=True)
                col1.info('Shift + click to change map pitch & angle.')
                col1.markdown(f"Note: Darker shades of Census tracts represent {var_dict1[variable]}. Greater sales volume represented by 'taller' census tracts.")
            with col3:
                subcol1, subcol2, subcol3 = st.columns([1, 1, 1])
                subcol1.metric(f"Median {variable}:", f"${KPI_dict[variable]}")
                subcol2.metric(f"{quarters[0]} to {quarters[1]} Change:", f"{kpi_delta()}%")
                subcol3.metric("Total Home Sales:", kpi_total_sales())
            col3.plotly_chart(line_chart(), use_container_width=True, config = {'displayModeBar': False})
except ValueError as e:
    if str(e).startswith('Number of class have to be an integer greater than or equal to 1'):
        col1.error('Insufficient data to run dashboard. Please expand search filters!')
    else:
        raise
        


# disclaimer to go at bottom of app
col1, col2, col3, col4, col5, col6 = st.columns([4, 1, 1, 1, 0.75, 0.75])
with col1:
    expander = st.expander("Disclaimers")
    expander.markdown("<span style='color:#022B3A'> Excludes non-qualified, non-market, and bulk transactions. Excludes transactions below $1,000 and homes smaller than 75 square feet. Data downloaded from Forsyth County public records on March 7, 2023.</span>", unsafe_allow_html=True)
image = Image.open('content/logo.png')
col6.write("")
col6.write("")
col6.write("Powered by:")
col6.image(image, width=80)
