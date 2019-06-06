########################################################################################################################
# Libraries
########################################################################################################################
import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html

import folium

import pandas as pd
import numpy as np
import plotly
import plotly.graph_objs as go
import datetime
from urllib.parse import quote
import os

########################################################################################################################
# Initialization
########################################################################################################################
css_url = 'https://codepen.io/Poster110/pen/LomzLx.css'
css_dash = 'https://codepen.io/chriddyp/pen/bWLwgP.css'
app = dash.Dash(name=__name__)
server = app.server
server.secret_key = os.environ.get('secret_key', 'secret')
app.css.append_css({
    "external_url": [css_dash, css_url],
})
layout_ini = go.Layout(paper_bgcolor='#01053c', plot_bgcolor='#01053c', font=dict(color='#ffffff'), height=700)
map_ini = folium.Map(location=(55, 15), zoom_start=3)


########################################################################################################################
# Import Data
########################################################################################################################
# Load Factor Data
df_data = pd.read_csv('Load_Factor_Europe_Wind.csv', low_memory=False)
list_country = df_data.columns[4:]
list_country = list_country.sort_values()
# GeoJson for the map
europe_geo = pd.read_json(open('Europe_Geojson.txt'))
# Get properties from the GeoJson
df_euro = pd.DataFrame()
for feature in europe_geo['features']:
    df_euro.loc[feature['properties']['iso_a2'], 'Code'] = feature['properties']['iso_a2']
    df_euro.loc[feature['properties']['iso_a2'], 'Name'] = feature['properties']['name']
# Get country location
df_pos = pd.read_json('Europe_Location_Geojson.json')
for country in list_country:
    pos = df_pos.loc[df_pos['cca2'] == country, 'latlng'].item()
    df_euro.loc[country, 'Lat'] = pos[0]
    df_euro.loc[country, 'Lon'] = pos[1]
# Country list
drop_country = []
for country in list_country:
    drop_country.append(df_euro.loc[df_euro['Code'] == country, 'Name'].item())


########################################################################################################################
# Global Functions
########################################################################################################################
def create_fig_load_year():
    df_data_y = pd.DataFrame()
    for df_gr in df_data.groupby('Year'):
        for country in df_gr[1][list_country]:
            df_data_y.loc[df_gr[0], country] = df_gr[1][country].mean()

    data = []
    for country in df_data_y.columns:
        trace = go.Scattergl(
            x=df_data_y.index,
            y=100 * df_data_y[country],
            name=df_euro.loc[df_euro['Code'] == country, 'Name'].item()
        )
        data.append(trace)

    layout = go.Layout(
        title='<b>Mean Load Factor per Country for 30 years</b>',
        xaxis=dict(
            title='Year'
        ),
        yaxis=dict(
            title='Load Factor [%]'
        ),
        paper_bgcolor='#01053c',
        plot_bgcolor='#01053c',
        font=dict(color='#ffffff')
    )

    fig_load_year = go.Figure(data=data, layout=layout)

    return fig_load_year


def template_download_plotly(fig):
    if 'data' in fig:
        fig_json = fig.to_plotly_json()
        fig_json['layout']['paper_bgcolor'] = '#ffffff'
        fig_json['layout']['plot_bgcolor'] = '#ffffff'
        fig_json['layout']['font']['color'] = '#000000'
        html_body = plotly.offline.plot(fig_json, include_plotlyjs=False, output_type='div')
        html_str = '''<html>
             <head>
                 <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
             </head>
             <body>
                 {}
             </body>
             </html>
             '''.format(html_body)
        html_str = "data:text/html;charset=utf-8," + quote(html_str)

        return html_str


def template_download_map(map_):

    return "data:text/html;charset=utf-8," + quote(map_)


fig_load_year = create_fig_load_year()


########################################################################################################################
# Comments
########################################################################################################################
md_ini = '''Following application has been made using data coming from https://setis.ec.europa.eu/EMHIRES-datasets.
Data have then been treated using Python on the Jupyter platform. Data are given on a hourly basis.

This application consists in graph presentation and short analysis. Purpose of this study is not to put
down wind energy. We can only optimize a process after measuring it.


Author: Bastien PRIEUR-GARROUSTE'''

md_load_30 = '''This graph represents the mean load factor in every european country for this last 30 years. The load 
factor represents the division between the power produced and the local capacity.

On this kind of graph, you are able to zoom in and out while dragging with your mouse. You also can filter each curve
while clicking on the wanted country in the legend.

Main point of this graph is the constance of the mean load factor for each country. Hierarchy between countries remains
also constant.


On the following slider, you can select the year of study. This will impact every following graph. Year is indicated 
in the title. You may have to refresh some of them to refresh the selected year.'''

md_map_load = '''This map represents the mean load factor in Europe for the selected year.

On this kind of map, you are able to zoom in and out. On hover, the load factor per country is given. Color scale
is given on the top of the map.

You are also free to download it. It will create a html file on your computer that you can easily open in your web
browser and share.'''

md_corr = '''This matrix represents the correlation factor between load factor of every european country.

Correlation factor indicates if both variables (here, load factors) have the same variations. Value goes from
0 to 1: 1  (red) meaning that both variables are perfectly correlated, 0 (blue) that they are independent.

While clicking on a cell, load factors along the year will be displayed on the right graph. Mean values for
each month is also provided. The white line represents the equation y=x.

A good correlation does not mean that two countries have the similar load factors but correlated variations. 
Nevertheless, good correlation factor here show evey time same load factor values. When a country has a low one, it is
rare that its neighbours have a high one.

Mediterraneans countries like Italy, Greece and Croatia seem to have the highest differences comparing to others european 
countries.'''

md_map_corr = '''This map presents the correlation factor between the selected country and the rest of Europe.
The lightest is the green, the less load factors are correlated. 

Concerning the circles, blue one represents the selected country. Green ones indicate a higher mean load factor
during the selected year. And red ones a lower one. Size also indicates the difference.

While selecting a country, the map and all following graphs will be updated.
'''

md_time_stat = '''Concerning the Europe data: the represented load factor does not represent the Europe load factor, 
but the mean value of every country.

On the left one, it is to notice that a huge difference between summer and winter, and this everywhere in Europe. 
This is actually a good point, electrical consumption is higher in winter due for example to house warming. I don't have
european data, but french ones are available on https://opendata.reseaux-energies.fr/pages/accueil/

On the right one, year time percentage for given load factor range is given. For example, in France 2015, the mean 
load factor was 28.58% of the time below 10%, and 56.06% of the time below 20%. Reminder: data are provided on a hourly
basis. For every country, curve are really similar. First bar (below 10%) is important. But in Europe (so, the mean 
value of all countries), this bar is much smaller. Load factor is more concentrated around a mean value (between 20% 
and 30%).'''

md_hour_basis = '''The 3 following graphs are linked.

The matrix represents for each country the difference between the yearly mean load factor value for each hour with the
yearly mean load factor. The first information to be noticed here is the global similar variations for all countries. 
Countries not following this trend (like Croatia or Slovenia) were the ones who also had no correlation with other 
european countries.

Moreover, unlike the monthly repartition, the trend is not following national daily electrical consumption. Again, I 
don't have european data available, but french ones are available here: 
https://www.rte-france.com/fr/eco2mix/eco2mix-consommation . A pic is occurring in the morning, between 8am and 10am. 
And a second one in the evening, for example.

While clicking on a cell, both following graph will be filled.'''

md_hour_scatter_left = '''This graph represents the difference for each day between the load factor at the selected 
hour and the monthly mean load factor. This monthly mean value is the same than the one plotted in the precedent graph.
Selected country is compared with mean Europe values.

For example, in France, 2015 at 1pm. The 2nd of January, load factor was smaller than the january expected mean load 
factor (around 19% for a 34.14% expected one). But globally in Europe, at the same time, this load factor was higher 
than expected (around 40% for a 34.5% expected one). Theoretically then, at this time, France could import electricity 
from Europe. When both difference have the same sign, however, electricity exchange may not be made.'''

md_hour_scatter_right = '''This graph put aside the time consideration. 

Points in the right top corner represent a positive difference for both selected country and Europe (so, when there is 
for the same day a green and yellow bar on the left graph). In this situation, there is too much produced electricity, 
a solution to store it has to be set. Points in the bottom left represent the times when electricity has to be 
unloaded.

In the bottom right, the selected country may export electricity while on the top left, it has to import it.

The red cross indicates the mean value, the ellipsis +/- the standard deviation. Red indicates that a storage solution 
has to be set and used. Green that exchange are possible between EU and selected country.'''

########################################################################################################################
# Layout
########################################################################################################################
app.layout = html.Div([
    html.Div(
        className='section',
        children=[
            html.H1('WIND ENERGY in EUROPE (1986 - 2015)', className='main_title')
        ]
    ),
    dcc.Markdown('---'),
    dcc.Markdown(
        md_ini,
        id='c_ini',
        className='main_comments',
    ),
    dcc.Markdown(
        'Load Factor in Europe',
        className='sub_title',
    ),
    dcc.Markdown(
        md_load_30,
        className='h_comments'
    ),
    html.Div(
        children=[
            dcc.Graph(
                id='fig_load_year',
                figure=fig_load_year
            )
        ]
    ),
    html.Div(
        children=[
            html.A(
                'Download this Graph',
                id='dl_fig_load_year',
                download="Graph_Load_Year.html",
                href=template_download_plotly(fig_load_year),
                target="_blank"
            )
        ],
        style={'margin-left': '87%'}
    ),
    html.Div(
        children=[
            dcc.Slider(
                id='sl_year',
                min=min(df_data['Year']),
                max=max(df_data['Year']),
                step=1,
                marks={i: '{}'.format(i) for i in range(min(df_data['Year']), max(df_data['Year']) + 1)},
                value=max(df_data['Year'])
            )
        ],
        style={'width': '95%', 'margin': 'auto'}
    ),
    html.Div(
        children=[
            html.Div(
                children=[
                    dcc.Markdown(
                        id='c_map_load',
                        children=[md_map_load],
                        className='comments'
                    )
                ],
                style={'width': '30%', 'display': 'inline-block', 'float': 'left', 'margin-left': '2.5%',
                       'margin-right': '2%'}
            ),
            html.Div(
                children=[
                    html.Iframe(
                        id='map_load',
                        srcDoc=map_ini.get_root().render(),
                        width='100%',
                        height='500'
                    )
                ],
                style={'width': '60%', 'display': 'inline-block', 'margin-left': '3%', 'margin-right': '2.5%'}
            )
        ]
    ),
    html.Div(
        children=[
            html.A(
                'Download this Map',
                id='dl_map_load_year',
                download="Map_Load_Year.html",
                href='',
                target="_blank"
            )
        ],
        style={'margin-left': '87%'}
    ),
    dcc.Markdown(
        'Load Factor Correlation',
        className='sub_title',
    ),
    dcc.Markdown(
        md_corr,
        className='h_comments'
    ),
    html.Div(
        children=[
            html.Div(
                children=[
                    dcc.Graph(
                        id='fig_heatmap',
                        figure={'layout': layout_ini}
                    )
                ],
                style={'width': '46%', 'display': 'inline-block', 'margin-left': '2.5%', 'margin-right': '1.5%'}
            ),
            html.Div(
                children=[
                    dcc.Graph(
                        id='fig_corr_sc',
                        figure={'layout': layout_ini}
                    )
                ],
                style={'width': '46%', 'display': 'inline-block', 'margin-left': '1.5%', 'margin-right': '2.5%'}
            )
        ]
    ),
    html.Div(
        children=[
            html.A(
                'Download this Graph',
                id='dl_heatmap',
                download="Heatmap_Corr.html",
                href="",
                target="_blank"
            )
        ],
        style={'width': '13%', 'display': 'inline-block', 'margin-left': '37%'}
    ),
    html.Div(
        children=[
            html.A(
                'Download this Graph',
                id='dl_fig_corr_sc',
                download="Graph_Corr.html",
                href="",
                target="_blank"
            )
        ],
        style={'width': '13%', 'display': 'inline-block', 'margin-left': '37%'}
    ),
    html.Div(
        children=[
            html.Div(
                children=[
                    dcc.Dropdown(
                        id='drop_country',
                        options=[{'label': x, 'value': x} for x in sorted(drop_country)],
                        value='France',
                        clearable=False
                    )
                ]
            ),
            dcc.Markdown(
                md_map_corr,
                id='c_map_corr',
                className='comments'
            )
        ],
        style={'width': '30%', 'display': 'inline-block', 'margin-left': '2.5%', 'margin-right': '1.5%',
               'float': 'left', 'margin-top': '40px'}
    ),
    html.Div(
        children=[
            html.Iframe(
                id='map_corr',
                srcDoc=map_ini.get_root().render(),
                width='100%',
                height='500'
            )
        ],
        style={'width': '62%', 'display': 'inline-block', 'margin-left': '1.5%', 'margin-right': '2.5%',
               'margin-top': '40px'}
    ),
    html.Div(
        children=[
            html.A(
                'Download this Map',
                id='dl_map_corr',
                download="Map_Corr.html",
                href="",
                target="_blank"
            )
        ],
        style={'width': '13%', 'display': 'inline-block', 'margin-left': '87%'}
    ),
    dcc.Markdown(
        'Time Statistics',
        className='sub_title',
    ),
    dcc.Markdown(
        md_time_stat,
        className='h_comments'
    ),
    html.Div(
        children=[
            dcc.Graph(
                id='fig_rep_month',
                figure={'layout': layout_ini}
            )
        ],
        style={'width': '46%', 'display': 'inline-block', 'margin-left': '2.5%', 'margin-right': '1.5%'}
    ),
    html.Div(
        children=[
            dcc.Graph(
                id='fig_rep_per',
                figure={'layout': layout_ini}
            )
        ],
        style={'width': '46%', 'display': 'inline-block', 'margin-left': '1.5%', 'margin-right': '2.5%'}
    ),
    html.Div(
        children=[
            html.A(
                'Download this Graph',
                id='dl_fig_rep_month',
                download="Graph_Rep_Month.html",
                href="",
                target="_blank"
            )
        ],
        style={'width': '13%', 'display': 'inline-block', 'margin-left': '37%'}
    ),
    html.Div(
        children=[
            html.A(
                'Download this Graph',
                id='dl_fig_rep_per',
                download="Graph_Percentage_Rep.html",
                href="",
                target="_blank"
            )
        ],
        style={'width': '13%', 'display': 'inline-block', 'margin-left': '37%'}
    ),
    dcc.Markdown(
        'Load Factor Repartition on a Hourly Basis',
        className='sub_title',
    ),
    dcc.Markdown(
        md_hour_basis,
        className='h_comments'
    ),
    html.Div(
        children=[
            dcc.Graph(
                id='fig_heatmap_hour',
                figure={'layout': layout_ini}
            )
        ],
        style={'width': '50%', 'margin-left': '25%', 'margin-right': '25%'}
    ),
    html.Div(
        children=[
            html.A(
                'Download this Graph',
                id='dl_heatmap_hour',
                download="Heatmap_Hour.html",
                href="",
                target="_blank"
            )
        ],
        style={'margin-left': '62%'}
    ),
    html.Div(
        children=[
            dcc.Graph(
                id='fig_heatmap_scatter',
                figure={'layout': layout_ini}
            )
        ],
        style={'width': '46%', 'display': 'inline-block', 'margin-left': '2.5%', 'margin-right': '1.5%'}
    ),
    html.Div(
        children=[
            dcc.Graph(
                id='fig_heatmap_versus',
                figure={'layout': layout_ini}
            )
        ],
        style={'width': '46%', 'display': 'inline-block', 'margin-left': '1.5%', 'margin-right': '2.5%'}
    ),
    html.Div(
        children=[
            html.A(
                'Download this Graph',
                id='dl_heatmap_scatter',
                download="Graph_Heatmap_Hour_Rep.html",
                href="",
                target="_blank"
            )
        ],
        style={'width': '13%', 'display': 'inline-block', 'margin-left': '37%'}
    ),
    html.Div(
        children=[
            html.A(
                'Download this Graph',
                id='dl_heatmap_versus',
                download="Graph_Heatmap_Hour_Versus.html",
                href="",
                target="_blank"
            )
        ],
        style={'width': '13%', 'display': 'inline-block', 'margin-left': '37%'}
    ),
    html.Div(
        dcc.Markdown(
            md_hour_scatter_left,
            className='comments'
        ),
        style={'width': '45%', 'margin-left': '2.5%', 'margin-right': '2.5%', 'display': 'inline-block'}
    ),
    html.Div(
        dcc.Markdown(
            md_hour_scatter_right,
            className='comments'
        ),
        style={'width': '45%', 'margin-left': '2.5%', 'display': 'inline-block'}
    ),
    dcc.Markdown(
        'Build your own Graph',
        className='sub_title',
    ),
    html.Div(
        children=[
            dcc.Markdown(
                'Country 1:',
                className='b_comments'
            ),
            dcc.Dropdown(
                id='drop_c_1',
                options=[{'label': x, 'value': x} for x in sorted(drop_country)],
                value='France',
                clearable=False
            ),
            dcc.Markdown(
                'Country 2:',
                className='b_comments'
            ),
            dcc.Dropdown(
                id='drop_c_2',
                options=[{'label': x, 'value': x} for x in sorted(drop_country)],
                value='Germany',
                clearable=False
            ),
            dcc.Markdown(
                children=['''Time range:'''],
                className='b_comments'
            ),
            dcc.RangeSlider(
                id='sl_range',
                min=min(df_data['Year']),
                max=max(df_data['Year']),
                step=1,
                value=[max(df_data['Year']) - 1, max(df_data['Year'])],
                marks={min(df_data['Year']): min(df_data['Year']), max(df_data['Year']): max(df_data['Year'])}
            ),
            dcc.Markdown(
                id='c_sl_range',
                children=['''{} - {}'''.format(max(df_data['Year']) - 1, max(df_data['Year']))],
                className='h_comments'
            ),
            dcc.Markdown(
                'Graph mode:',
                className='b_comments'
            ),
            dcc.Dropdown(
                id='drop_type',
                options=[{'label': x, 'value': x} for x in ['Scatter', 'Versus', 'LF Rep.', 'Time Rep.', 'Stacked']],
                value='Scatter',
                clearable=False
            ),
            dcc.Markdown(
                'Time filter:',
                className='b_comments'
            ),
            dcc.Dropdown(
                id='drop_filter',
                options=[{'label': x, 'value': x} for x in ['Year', 'Month', 'Day', 'Hour']],
                value='Year',
                clearable=False
            ),
            dcc.Markdown(
                'Provide data:',
                className='b_comments'
            ),
            dcc.Dropdown(
                id='drop_sample',
                options=[{'label': x, 'value': x} for x in ['All', 'Mean']],
                value='Mean',
                clearable=False
            ),
            html.Div(
                children=[
                    html.A(
                        'Download this Graph',
                        id='dl_fig_cr',
                        download="Graph_Custom.html",
                        href="",
                        target="_blank"
                    )
                ],
                style={'margin-bottom': '75px'}
            )
        ],
        style={'width': '30%', 'display': 'inline-block', 'margin-left': '2.5%', 'margin-right': '1.5%',
               'margin-top': '50px', 'float': 'left'}
    ),
    html.Div(
        children=[
            dcc.Graph(
                id='fig_cr',
                figure={'layout': layout_ini}
            )
        ],
        style={'width': '62%', 'margin-left': '1.5%', 'margin-right': '2.5%', 'display': 'inline-block'}
    )
])


########################################################################################################################
# Year Selection
########################################################################################################################
@app.callback([Output('map_load', 'srcDoc'),
               Output('fig_heatmap', 'figure'),
               Output('fig_heatmap_hour', 'figure'),
               Output('dl_heatmap', 'href'),
               Output('dl_heatmap_hour', 'href'),
               Output('dl_map_load_year', 'href')],
              [Input('sl_year', 'value')])
def year_choice(ch_year):
    str_map_load = create_map_load(ch_year)
    fig_heatmap = create_heatmap(ch_year)
    fig_heatmap_hour = create_heatmap_hour(ch_year)

    html_fig_heatmap = template_download_plotly(fig_heatmap)
    html_fig_heatmap_hour = template_download_plotly(fig_heatmap_hour)

    return str_map_load, fig_heatmap, fig_heatmap_hour, html_fig_heatmap, html_fig_heatmap_hour, \
           template_download_map(str_map_load)


def create_map_load(ch_year):
    map_euro_load = folium.Map(location=(55, 15), zoom_start=3)

    df_map_load = pd.DataFrame()
    for country in list_country:
        df_map_load.loc[country, 'Load_Factor'] = 100 * df_data.loc[df_data['Year'] == ch_year, country].mean()

    for feature in europe_geo['features']:
        isoa2 = feature['properties']['iso_a2']
        if isoa2 in df_map_load.index:
            feature['properties']['Load Factor'] = str(round(df_map_load['Load_Factor'][isoa2], 1))+  '%'
            feature['properties']['Country'] = feature['properties']['name']
        else:
            feature['properties']['Load Factor'] = ''

    str_ = europe_geo['features'].to_json()
    for idx in range(0, len(europe_geo.index)):
        str_ = str_.replace('"{}":'.format(idx), '')
    str_ = '{"type":"FeatureCollection","features":[' + str_[1:-1] + ']}'

    map_geojson = folium.Choropleth(
        geo_data=str_,
        name='choropleth',
        data=df_map_load,
        columns=[df_map_load.index, 'Load_Factor'],
        key_on='properties.iso_a2',
        fill_color='YlGn',
        fill_opacity=0.7,
        nan_fill_opacity=0.1,
        line_opacity=0.2,
        highlight=True,
        legend_name='Load Factor in {} [%]'.format(ch_year)
    )

    folium.GeoJsonTooltip(
        fields=['Country', 'Load Factor']
    ).add_to(map_geojson.geojson)

    map_geojson.add_to(map_euro_load)

    return map_euro_load.get_root().render()


def create_heatmap(ch_year):
    # Get correlation
    df_data_corr = df_data.loc[df_data['Year'] == ch_year, list_country].corr()

    z = []
    for col in df_data_corr.columns:
        z.append(df_data_corr[col])

    # Heatmap Plot
    data = [go.Heatmap(
        x=df_data_corr.index,
        y=df_data_corr.columns,
        z=z,
        xgap=1,
        ygap=1,
        showscale=True
    )]

    layout = go.Layout(
        title='<b>Load Factor Correlation between Countries in {}</b>'.format(ch_year),
        xaxis=dict(
            title='Country'
        ),
        yaxis=dict(
            title='Country'
        ),
        height=700,
        margin=dict(l=50, r=0),
        paper_bgcolor='#01053c',
        plot_bgcolor='#ffffff',
        font=dict(color='#ffffff')
    )

    fig_heatmap = go.Figure(data=data, layout=layout)

    return fig_heatmap


def create_heatmap_hour(ch_year):
    # Get correlation
    df_data_hour = pd.DataFrame()
    for df_gr in df_data.loc[df_data['Year'] == ch_year].groupby('Hour'):
        for country in list_country:
            mean_lf = 100 * df_data.loc[df_data['Year'] == ch_year, country].mean()
            df_data_hour.loc[df_gr[0], country] = 100 * df_gr[1][country].mean() - mean_lf

    z = []
    for col in df_data_hour.columns:
        z.append(df_data_hour[col])

    # Heatmap Plot
    data = [go.Heatmap(
        x=df_data_hour.index,
        y=df_data_hour.columns,
        z=z,
        xgap=1,
        ygap=1,
        showscale=True
    )]

    layout = go.Layout(
        title='<b>Load Factor per Hour in {}</b>'.format(ch_year),
        xaxis=dict(
            title='Hour'
        ),
        yaxis=dict(
            title='Country'
        ),
        height=700,
        margin=dict(l=50, r=0),
        paper_bgcolor='#01053c',
        plot_bgcolor='#ffffff',
        font=dict(color='#ffffff')
    )

    fig_heatmap_hour = go.Figure(data=data, layout=layout)

    return fig_heatmap_hour


########################################################################################################################
# Correlation Heatmap click
########################################################################################################################
@app.callback([Output('fig_corr_sc', 'figure'),
               Output('dl_fig_corr_sc', 'href')],
              [Input('fig_heatmap', 'clickData')],
              [State('sl_year', 'value')])
def fill_scatter(sel_pt, ch_year):
    if sel_pt is not None:
        country_1 = df_euro.loc[df_euro['Code'] == sel_pt['points'][0]['x'], 'Name'].item()
        country_2 = df_euro.loc[df_euro['Code'] == sel_pt['points'][0]['y'], 'Name'].item()

        df_month = pd.DataFrame()
        for df_gr in df_data.loc[df_data['Year'] == ch_year].groupby('Month'):
            month = datetime.date(1900, df_gr[0], 1).strftime('%B')
            df_month.loc[month, 'LF_1'] = 100 * df_gr[1][sel_pt['points'][0]['x']].mean()
            df_month.loc[month, 'LF_2'] = 100 * df_gr[1][sel_pt['points'][0]['y']].mean()

        df_data_s = df_data.loc[df_data['Year'] == ch_year, list_country]
        data = [
            go.Scattergl(
                x=100 * df_data_s[sel_pt['points'][0]['x']],
                y=100 * df_data_s[sel_pt['points'][0]['y']],
                mode='markers',
                marker=dict(
                    color='green'
                ),
                name='Whole Period'
            ),
            go.Scattergl(
                x=df_month['LF_1'],
                y=df_month['LF_2'],
                text=list(df_month.index),
                mode='markers',
                marker=dict(
                    color='red',
                    size=8
                ),
                name='Months',
                hoverinfo='text'
            ),
        ]

        tab_ann = []
        for month in df_month.index:
            ann = dict(x=df_month['LF_1'][month], y=df_month['LF_2'][month], xref='x', yref='y', text=month, showarrow=True,
                       align='center', font=dict(color='#ffffff'), arrowhead=2, arrowsize=1, arrowwidth=2,
                       arrowcolor='#000000', ax=-30, ay=-30,
                       bordercolor='#c7c7c7', borderwidth=2, borderpad=4, bgcolor='#000000', opacity=0.8)
            tab_ann.append(ann)

        end_sh = min(max(data[0]['x']), max(data[0]['y']))
        layout = go.Layout(
            title='<b>Load Factor between {} and {} in {}<b>'.format(country_1, country_2, ch_year),
            xaxis=dict(
                title='Load Factor {} [%]'.format(country_1)
            ),
            yaxis=dict(
                title='Load Factor {} [%]'.format(country_2)
            ),
            height=700,
            annotations=tab_ann,
            hovermode='closest',
            legend=dict(
                x=.35,
                y=1.02,
                orientation="h"
            ),
            margin=dict(l=40, r=0),
            paper_bgcolor='#01053c',
            plot_bgcolor='#01053c',
            shapes=[dict(type='line', xref='x', yref='y', x0=0, x1=end_sh, y0=0, y1=end_sh,
                         line=dict(color='white'))],
            font=dict(color='#ffffff')
        )

        fig_corr_sc = go.Figure(data=data, layout=layout)
        html_fig_corr_sc = template_download_plotly(fig_corr_sc)

    else:

        fig_corr_sc = go.Figure(layout=layout_ini)
        fig_corr_sc.layout.title.text = '<b>Load Factor between 2 Countries<b>'
        html_fig_corr_sc = ''

    return fig_corr_sc, html_fig_corr_sc


########################################################################################################################
# Hour Heatmap click
########################################################################################################################
@app.callback([Output('fig_heatmap_scatter', 'figure'),
               Output('fig_heatmap_versus', 'figure'),
               Output('dl_heatmap_scatter', 'href'),
               Output('dl_heatmap_versus', 'href')],
              [Input('fig_heatmap_hour', 'clickData')],
              [State('sl_year', 'value')])
def fill_graph_hour(sel_pt, ch_year):
    if sel_pt is not None:
        country_code = sel_pt['points'][0]['y']
        country_name = df_euro.loc[df_euro['Code'] == country_code, 'Name'].item()
        sel_hour = sel_pt['points'][0]['x']

        # Set Time as index
        df_scatter = df_data.loc[(df_data['Year'] == ch_year) & (df_data['Hour'] == sel_hour), df_data.columns]
        df_scatter['Time'] = df_scatter['Year'].apply(str) + '/' + df_scatter['Month'].apply(str) + '/' + df_scatter[
            'Day'].apply(str) + ' ' + str(sel_hour) + ':00:00'
        df_scatter['Time'] = pd.to_datetime(df_scatter['Time'], format='%Y/%m/%d %H:%M:%S')
        df_scatter.set_index('Time', inplace=True)

        # 'Mean' columns represents the mean load factor per month for each country
        for df_gr in df_data.loc[df_data['Year'] == ch_year, df_data.columns].groupby('Month'):
            month = df_gr[0]
            df_scatter.loc[df_scatter['Month'] == month, 'Mean'] = 100 * df_gr[1][country_code].mean()
            df_scatter.loc[df_scatter['Month'] == month, 'Mean_EU'] = 100 * df_gr[1][list_country].mean(axis=1).mean()

        # 'Diff' represents the difference between the load factor at selected hour and the monthly mean value
        df_scatter['Diff'] = 100 * df_scatter[country_code] - df_scatter['Mean']
        df_scatter['Diff_EU'] = 100 * df_scatter.loc[:, list_country].mean(axis=1) - df_scatter['Mean_EU']
        df_scatter['Color'] = np.where(df_scatter['Diff'] > 0, 'green', 'red')
        df_scatter['Color_EU'] = np.where(df_scatter['Diff_EU'] > 0, 'yellow', 'magenta')

        fig_scatter_hour = fill_bar_hour(ch_year, country_name, sel_hour, df_scatter)
        fig_scatter_versus = fill_scatter_versus(ch_year, country_name, sel_hour, df_scatter)

        html_fig_scatter_hour = template_download_plotly(fig_scatter_hour)
        html_fig_scatter_versus = template_download_plotly(fig_scatter_versus)

    else:

        fig_scatter_hour = go.Figure(layout=layout_ini)
        fig_scatter_versus = go.Figure(layout=layout_ini)

        html_fig_scatter_hour = ''
        html_fig_scatter_versus = ''

    return fig_scatter_hour, fig_scatter_versus, html_fig_scatter_hour, html_fig_scatter_versus


def fill_bar_hour(ch_year, country_name, sel_hour, df_scatter):

    df_sc_pos_c = df_scatter.loc[df_scatter['Diff'] >= 0, df_scatter.columns]
    df_sc_neg_c = df_scatter.loc[df_scatter['Diff'] < 0, df_scatter.columns]
    df_sc_pos_eu = df_scatter.loc[df_scatter['Diff_EU'] >= 0, df_scatter.columns]
    df_sc_neg_eu = df_scatter.loc[df_scatter['Diff_EU'] < 0, df_scatter.columns]

    data = [
        go.Bar(
            x=df_sc_pos_c.index,
            y=df_sc_pos_c['Diff'],
            name='Diff {} > 0'.format(country_name),
            marker=dict(
                color=df_sc_pos_c['Color']
            ),
            legendgroup='country'
        ),
        go.Bar(
            x=df_sc_neg_c.index,
            y=df_sc_neg_c['Diff'],
            name='Diff {} < 0'.format(country_name),
            marker=dict(
                color=df_sc_neg_c['Color']
            ),
            legendgroup='country'
        ),
        go.Bar(
            x=df_sc_pos_eu.index,
            y=df_sc_pos_eu['Diff_EU'],
            name='Diff EU > 0',
            marker=dict(
                color=df_sc_pos_eu['Color_EU']
            ),
            legendgroup='EU'
        ),
        go.Bar(
            x=df_sc_neg_eu.index,
            y=df_sc_neg_eu['Diff_EU'],
            name='Diff EU < 0',
            marker=dict(
                color=df_sc_neg_eu['Color_EU']
            ),
            legendgroup='EU'
        ),
        go.Scattergl(
            x=df_scatter.index,
            y=df_scatter['Mean'],
            name='Month Mean {}'.format(country_name),
            mode='lines',
            line=dict(
                color='white'
            ),
            yaxis='y2',
            legendgroup='country'
        ),
        go.Scattergl(
            x=df_scatter.index,
            y=df_scatter['Mean_EU'],
            name='Month Mean EU',
            mode='lines',
            line=dict(
                color='aqua'
            ),
            yaxis='y2',
            legendgroup='EU'
        )
    ]

    layout = go.Layout(
        title='<b>Load Factor Repartition at {}h in {} in {}</b>'.format(sel_hour, country_name, ch_year),
        xaxis=dict(
            title='Time [GMT]'
        ),
        yaxis=dict(
            title='Load Factor Difference [%]'
        ),
        yaxis2=dict(
            title='Mean Load Factor per Month [%]',
            side='right',
            overlaying='y',
            showgrid=False,
            rangemode='tozero'
        ),
        legend=dict(
            x=.35,
            y=1.1,
            orientation="h"
        ),
        height=650,
        margin=dict(l=40, r=40),
        paper_bgcolor='#01053c',
        plot_bgcolor='#01053c',
        font=dict(color='#ffffff')
    )

    fig_scatter_hour = go.Figure(data=data, layout=layout)

    return fig_scatter_hour


def fill_scatter_versus(ch_year, country_name, sel_hour, df_scatter):
    sh_c = [df_scatter['Diff'].mean(), df_scatter['Diff_EU'].mean()]
    sh_std = [df_scatter['Diff'].std(), df_scatter['Diff_EU'].std()]
    if sh_c[0] * sh_c[1] > 0:
        sh_color = 'red'
    else:
        sh_color = 'green'

    data = [
        go.Scatter(
            x=[sh_c[0]],
            y=[sh_c[1]],
            name='Mean',
            mode='markers',
            marker=dict(
                symbol='cross',
                color=sh_color,
                size=12
            ),
            showlegend=False
        )
    ]

    for df_gr in df_scatter.groupby('Month'):
        trace = go.Scattergl(
            x=df_gr[1]['Diff'],
            y=df_gr[1]['Diff_EU'],
            mode='markers',
            text=list(df_gr[1].index),
            hoverinfo='text',
            name=datetime.date(1900, df_gr[0], 1).strftime('%B'),
        )
        data.append(trace)

    layout = go.Layout(
        title='<b>Load Factor Points at {}h in {} in {}</b>'.format(sel_hour, country_name, ch_year),
        xaxis=dict(
            title='Difference {}'.format(country_name)
        ),
        yaxis=dict(
            title='Difference EU'
        ),
        height=650,
        margin=dict(l=40, r=40),
        hovermode='closest',
        paper_bgcolor='#01053c',
        plot_bgcolor='#01053c',
        font=dict(color='#ffffff'),
        shapes=[dict(type='circle', xref='x', yref='y', x0=sh_c[0] - sh_std[0], x1=sh_c[0] + sh_std[0],
                    y0=sh_c[1] - sh_std[1], y1=sh_c[1] + sh_std[1], fillcolor=sh_color, opacity=0.3)]
    )

    fig_scatter_versus = go.Figure(data=data, layout=layout)

    return fig_scatter_versus


########################################################################################################################
# Country Selection
########################################################################################################################
@app.callback([Output('map_corr', 'srcDoc'),
               Output('fig_rep_month', 'figure'),
               Output('fig_rep_per', 'figure'),
               Output('dl_fig_rep_month', 'href'),
               Output('dl_fig_rep_per', 'href'),
               Output('dl_map_corr', 'href')],
              [Input('drop_country', 'value'),
               Input('sl_year', 'value')])
def country_choice(ch_country, ch_year):

    map_corr_str = create_map_corr(ch_year, ch_country)
    fig_rep_month = create_fig_rep_month(ch_year, ch_country)
    fig_rep_per = create_fig_rep_per(ch_year, ch_country)

    html_fig_rep_month = template_download_plotly(fig_rep_month)
    html_fig_rep_per = template_download_plotly(fig_rep_per)

    return map_corr_str, fig_rep_month, fig_rep_per, html_fig_rep_month, html_fig_rep_per, \
           template_download_map(map_corr_str)


def create_map_corr(ch_year, ch_country):
    ch_country_code = df_euro.loc[df_euro['Name'] == ch_country, 'Code'].item()

    map_corr = folium.Map(location=(55, 15), zoom_start=3)
    df_data_corr = df_data.loc[df_data['Year'] == ch_year, list_country].corr()

    for feature in europe_geo['features']:
        isoa2 = feature['properties']['iso_a2']
        if isoa2 in df_data_corr.columns:
            feature['properties']['Corr. Factor'] = str(round(df_data_corr[ch_country_code][isoa2], 2))
            feature['properties']['Load Factor'] = str(round(100 * df_data.loc[df_data['Year'] == ch_year,
                                                                               isoa2].mean(), 1)) + '%'
            feature['properties']['Country'] = feature['properties']['name']
        else:
            feature['properties']['Corr. Factor'] = ''
            feature['properties']['Load Factor'] = ''
            feature['properties']['Country'] = feature['properties']['name']

    str_ = europe_geo['features'].to_json()
    for idx in range(0, len(europe_geo.index)):
        str_ = str_.replace('"{}":'.format(idx), '')
    str_ = '{"type":"FeatureCollection","features":[' + str_[1:-1] + ']}'

    map_geojson = folium.Choropleth(
        geo_data=str_,
        name='choropleth',
        data=df_data_corr,
        columns=[df_data_corr.index, ch_country_code],
        key_on='properties.iso_a2',
        fill_color='YlGn',
        fill_opacity=0.7,
        line_opacity=0.2,
        nan_fill_opacity=0.1,
        highlight=True,
        legend_name='Load Factor Correlation Factor between {} and Countries in {}'.format(ch_country, ch_year)
    )

    folium.GeoJsonTooltip(
        fields=['Country', 'Corr. Factor', 'Load Factor']
    ).add_to(map_geojson.geojson)

    map_geojson.add_to(map_corr)

    lf_ch_country = 100 * df_data.loc[df_data['Year'] == ch_year, ch_country_code].mean()
    folium.CircleMarker(
        location=[df_euro.loc[df_euro['Code'] == ch_country_code, 'Lat'].item(),
                  df_euro.loc[df_euro['Code'] == ch_country_code, 'Lon'].item()],
        radius=10,
        color='blue',
        fill=True,
        fill_color='blue'
    ).add_to(map_corr)

    for country in list_country:
        if country != ch_country_code:
            lf_country = 100 * df_data.loc[df_data['Year'] == ch_year, country].mean()
            if lf_country < lf_ch_country:
                c_color = 'red'
            else:
                c_color = 'green'
            folium.CircleMarker(
                location=[df_euro.loc[df_euro['Code'] == country, 'Lat'].item(),
                          df_euro.loc[df_euro['Code'] == country, 'Lon'].item()],
                radius=max(1, 10 + lf_country - lf_ch_country),
                color=c_color,
                fill=True,
                fill_color=c_color
            ).add_to(map_corr)

    return map_corr.get_root().render()


def create_fig_rep_month(ch_year, ch_country):
    ch_country_code = df_euro.loc[df_euro['Name'] == ch_country, 'Code'].item()

    df_load_month = pd.DataFrame()
    for df_gr in df_data.loc[df_data['Year'] == ch_year].groupby('Month'):
        month = datetime.date(1900, df_gr[0], 1).strftime('%B')
        df_temp = df_gr[1][list_country]
        df_load_month.loc[month, 'LF_EU'] = 100 * df_temp.mean(axis=1).mean()
        df_load_month.loc[month, 'LF_Country'] = 100 * df_gr[1][ch_country_code].mean()

    data = [
        go.Bar(
            x=df_load_month.index,
            y=df_load_month['LF_EU'],
            text=list(round(df_load_month['LF_EU'], 2)),
            name='Europe',
            textposition='auto',
            hoverinfo='y',
            marker=dict(
                color='rgb(225, 202,158)',
                line=dict(
                    color='rgb(107,48,8)',
                    width=1.5),
            ),
            opacity=0.8
        ),
        go.Bar(
            x=df_load_month.index,
            y=df_load_month['LF_Country'],
            text=list(round(df_load_month['LF_Country'], 2)),
            name=ch_country,
            textposition='auto',
            hoverinfo='y',
            marker=dict(
                color='rgb(202, 225, 158)',
                line=dict(
                    color='rgb(48, 107, 8)',
                    width=1.5),
            ),
            opacity=0.8
        ),
    ]

    layout = go.Layout(
        title='<b>Mean Load Factor per Month in {}</b>'.format(ch_year),
        xaxis=dict(
            title='Month'
        ),
        yaxis=dict(
            title='Load Factor [%]'
        ),
        legend=dict(
            x=.35,
            y=1.1,
            orientation="h"
        ),
        height=500,
        margin=dict(l=40, r=0),
        paper_bgcolor='#01053c',
        plot_bgcolor='#01053c',
        font=dict(color='#ffffff')
    )

    fig_rep_month = go.Figure(data=data, layout=layout)

    return fig_rep_month


def create_fig_rep_per(ch_year, ch_country):
    ch_country_code = df_euro.loc[df_euro['Name'] == ch_country, 'Code'].item()

    list_per = np.linspace(10, 100, num=10)
    df_data_rep = df_data.loc[df_data['Year'] == ch_year, list_country]
    df_data_rep['Mean'] = df_data_rep.mean(axis=1)

    df_rep = pd.DataFrame()
    for per in list_per:
        df_rep.loc[per, 'EU'] = 100 * len(df_data_rep.loc[100 * df_data_rep['Mean'] <= per]) / len(df_data_rep)
        df_rep.loc[per, 'Country'] = 100 * len(df_data_rep.loc[100 * df_data_rep[ch_country_code] <= per]) / len(
            df_data_rep)

    data = [
        go.Bar(
            x=df_rep.index,
            y=df_rep['EU'],
            text=list(round(df_rep['EU'], 2)),
            textposition='auto',
            hoverinfo='y',
            name='Europe',
            marker=dict(
                color='rgb(225, 202,158)',
                line=dict(
                    color='rgb(107,48,8)',
                    width=1.5),
            ),
            opacity=0.8
        ),
        go.Bar(
            x=df_rep.index,
            y=df_rep['Country'],
            text=list(round(df_rep['Country'], 2)),
            textposition='auto',
            hoverinfo='y',
            name=ch_country,
            marker=dict(
                color='rgb(202, 225, 158)',
                line=dict(
                    color='rgb(48, 107, 8)',
                    width=1.5),
            ),
            opacity=0.8
        ),
    ]

    layout = go.Layout(
        title='<b>Load Factor Repartition in {}</b>'.format(ch_year),
        xaxis=dict(
            title='Load Factor [%]'
        ),
        yaxis=dict(
            title='Time Percentage [%]'
        ),
        legend=dict(
            x=.35,
            y=1.1,
            orientation="h"
        ),
        margin=dict(l=40, r=0),
        height=500,
        paper_bgcolor='#01053c',
        plot_bgcolor='#01053c',
        font=dict(color='#ffffff')
    )

    fig_rep_per = go.Figure(data=data, layout=layout)

    return fig_rep_per


########################################################################################################################
# Custom Graph Creation
########################################################################################################################
@app.callback([Output('fig_cr', 'figure'),
               Output('dl_fig_cr', 'href')],
              [Input('drop_c_1', 'value'),
               Input('drop_c_2', 'value'),
               Input('sl_range', 'value'),
               Input('drop_type', 'value'),
               Input('drop_filter', 'value'),
               Input('drop_sample', 'value')])
def create_custom_graph(country_1, country_2, time_range, gr_type, gr_filter, gr_sample):
    if gr_type == 'Scatter':
        fig_cr = create_scatter(country_1, country_2, time_range, gr_filter)
    elif gr_type == 'Versus':
        fig_cr = create_versus(country_1, country_2, time_range, gr_filter, gr_sample)
    elif gr_type == 'LF Rep.':
        fig_cr = create_lfrep(country_1, country_2, time_range)
    elif gr_type == 'Time Rep.':
        fig_cr = create_trep(country_1, country_2, time_range, gr_filter, gr_sample)
    elif gr_type == 'Stacked':
        fig_cr = create_stacked(country_1, time_range, gr_filter, gr_sample)
    else:
        fig_cr = go.Figure(layout=layout_ini)

    html_fig = template_download_plotly(fig_cr)

    return fig_cr, html_fig


def create_scatter(country_1, country_2, time_range, gr_filter):

    if gr_filter == 'Year':
        sample = 'A'
    elif gr_filter == 'Month':
        sample = 'M'
    else:
        sample = 'D'

    country_1_code = df_euro.loc[df_euro['Name'] == country_1, 'Code'].item()
    country_2_code = df_euro.loc[df_euro['Name'] == country_2, 'Code'].item()

    df_scatter = df_data.loc[(df_data['Year'] >= time_range[0]) & (df_data['Year'] <= time_range[1]),
                             [country_1_code, country_2_code, 'Year', 'Month', 'Day']]
    df_scatter['Time'] = df_scatter['Year'].apply(str) + '/' + df_scatter['Month'].apply(str) + '/' + \
                         df_scatter['Day'].apply(str)
    df_scatter['Time'] = pd.to_datetime(df_scatter['Time'], format='%Y/%m/%d')
    df_scatter.set_index('Time', inplace=True)
    df_scatter = df_scatter.resample(sample).mean()

    data = []
    for country in [country_1_code, country_2_code]:
        trace = go.Scattergl(
            x=df_scatter.index,
            y=100 * df_scatter[country],
            mode='lines',
            name=df_euro.loc[df_euro['Code'] == country, 'Name'].item()
        )
        data.append(trace)

    layout = go.Layout(
        title='<b>Mean Load Factor per {} for {} and {} from {} to {}</b>'.format(gr_filter, country_1, country_2,
                                                                                time_range[0], time_range[1]),
        xaxis=dict(
            title='Time'
        ),
        yaxis=dict(
            title='Load Factor [%]'
        ),
        legend=dict(
            x=.35,
            y=1.1,
            orientation="h"
        ),
        margin=dict(l=40, r=0),
        height=650,
        paper_bgcolor='#01053c',
        plot_bgcolor='#01053c',
        font=dict(color='#ffffff')
    )

    fig_cr = go.Figure(data=data, layout=layout)

    return fig_cr


def create_versus(country_1, country_2, time_range, gr_filter, gr_sample):
    country_1_code = df_euro.loc[df_euro['Name'] == country_1, 'Code'].item()
    country_2_code = df_euro.loc[df_euro['Name'] == country_2, 'Code'].item()

    if gr_filter == 'Year':
        sample = 'A'
    elif gr_filter == 'Month':
        sample = 'M'
    else:
        sample = 'D'

    df_vs = df_data.loc[(df_data['Year'] >= time_range[0]) & (df_data['Year'] <= time_range[1]),
                        [country_1_code, country_2_code, 'Year', 'Month', 'Day', 'Hour']]

    df_vs['Time'] = df_vs['Year'].apply(str) + '/' + df_vs['Month'].apply(str) + '/' + df_vs['Day'].apply(str)
    df_vs['Time'] = pd.to_datetime(df_vs['Time'], format='%Y/%m/%d')
    df_vs.set_index('Time', inplace=True)
    if gr_sample == 'All':
        df_vs_s = df_vs
    else:
        df_vs_s = df_vs.resample(sample).mean()

    data = [
        go.Scattergl(
            x=100 * df_vs_s[country_1_code],
            y=100 * df_vs_s[country_2_code],
            name='Whole Period',
            text=list(df_vs_s.index),
            mode='markers',
            marker=dict(
                color='green',
                size=5
            ),
            hoverinfo='text'
        )
    ]

    df_filter = pd.DataFrame()
    for df_gr in df_vs.groupby(gr_filter):
        for country in [country_1_code, country_2_code]:
            if gr_filter == 'Month':
                idx = datetime.date(1900, df_gr[0], 1).strftime('%B')
            else:
                idx = df_gr[0]
            df_filter.loc[idx, country] = 100 * df_gr[1][country].mean()

    data.append(
        go.Scattergl(
            x=df_filter[country_1_code],
            y=df_filter[country_2_code],
            mode='markers',
            text=list(df_filter.index),
            marker=dict(
                color='red',
                size=8
            ),
            name=gr_filter,
            hoverinfo='text'
        )
    )

    tab_ann = []
    for filter in df_filter.index:
        ann = dict(x=df_filter[country_1_code][filter], y=df_filter[country_2_code][filter], xref='x', yref='y',
                   text=filter, showarrow=True, align='center', font=dict(color='#ffffff'), arrowhead=2, arrowsize=1,
                   arrowwidth=2, arrowcolor='#000000', ax=-30, ay=-30, bordercolor='#c7c7c7', borderwidth=2,
                   borderpad=4, bgcolor='#000000', opacity=0.8)
        tab_ann.append(ann)

    end_sh = min(max(data[0]['x']), max(data[0]['y']))
    layout = go.Layout(
        title='<b>Load Factor between {} and {} from {} to {}<b>'.format(country_1, country_2, time_range[0],
                                                                         time_range[1]),
        xaxis=dict(
            title='Load Factor {} [%]'.format(country_1)
        ),
        yaxis=dict(
            title='Load Factor {} [%]'.format(country_2)
        ),
        height=650,
        annotations=tab_ann,
        hovermode='closest',
        legend=dict(
            x=.35,
            y=1.1,
            orientation="h"
        ),
        margin=dict(l=40, r=0),
        paper_bgcolor='#01053c',
        plot_bgcolor='#01053c',
        shapes=[dict(type='line', xref='x', yref='y', x0=0, x1=end_sh, y0=0, y1=end_sh,
                     line=dict(color='white'))],
        font=dict(color='#ffffff')
    )

    fig_cr = go.Figure(data=data, layout=layout)

    return fig_cr


def create_lfrep(country_1, country_2, time_range):
    country_1_code = df_euro.loc[df_euro['Name'] == country_1, 'Code'].item()
    country_2_code = df_euro.loc[df_euro['Name'] == country_2, 'Code'].item()

    df_rep_ini = df_data.loc[(df_data['Year'] >= time_range[0]) & (df_data['Year'] <= time_range[1]),
                             [country_1_code, country_2_code]]

    df_lfrep = pd.DataFrame()
    list_per = np.linspace(10, 100, num=10)
    for per in list_per:
        for country in [country_1_code, country_2_code]:
            df_lfrep.loc[per, country] = 100 * len(df_rep_ini.loc[100 * df_rep_ini[country] <= per, country]) / len(
                df_rep_ini)

    data = [
        go.Bar(
            x=df_lfrep.index,
            y=df_lfrep[country_1_code],
            text=list(round(df_lfrep[country_1_code], 2)),
            textposition='auto',
            hoverinfo='y',
            name=country_1,
            marker=dict(
                color='rgb(225, 202,158)',
                line=dict(
                    color='rgb(107,48,8)',
                    width=1.5),
            ),
            opacity=0.8
        ),
        go.Bar(
            x=df_lfrep.index,
            y=df_lfrep[country_2_code],
            text=list(round(df_lfrep[country_2_code], 2)),
            textposition='auto',
            hoverinfo='y',
            name=country_2,
            marker=dict(
                color='rgb(202, 225, 158)',
                line=dict(
                    color='rgb(48, 107, 8)',
                    width=1.5),
            ),
            opacity=0.8
        ),
    ]

    layout = go.Layout(
        title='<b>Load Factor Repartition from {} to {}</b>'.format(time_range[0], time_range[1]),
        xaxis=dict(
            title='Load Factor [%]'
        ),
        yaxis=dict(
            title='Time Percentage [%]'
        ),
        legend=dict(
            x=.35,
            y=1.1,
            orientation="h"
        ),
        margin=dict(l=40, r=0),
        height=650,
        paper_bgcolor='#01053c',
        plot_bgcolor='#01053c',
        font=dict(color='#ffffff')
    )

    fig_cr = go.Figure(data=data, layout=layout)

    return fig_cr


def create_trep(country_1, country_2, time_range, gr_filter, gr_sample):
    country_1_code = df_euro.loc[df_euro['Name'] == country_1, 'Code'].item()
    country_2_code = df_euro.loc[df_euro['Name'] == country_2, 'Code'].item()

    df_trep_ini = df_data.loc[(df_data['Year'] >= time_range[0]) & (df_data['Year'] <= time_range[1]),
                              [country_1_code, country_2_code, 'Year', 'Month', 'Day', 'Hour']]

    df_trep = pd.DataFrame()
    if gr_sample == 'Mean':
        for df_gr in df_trep_ini.groupby(gr_filter):
            if gr_filter == 'Month':
                idx = datetime.date(1900, df_gr[0], 1).strftime('%B')
            else:
                idx = df_gr[0]
            for country in [country_1_code, country_2_code]:
                df_trep.loc[idx, country] = df_gr[1][country].mean()
    else:
        if gr_filter == 'Year':
            sample = 'A'
        elif gr_filter == 'Month':
            sample = 'M'
        else:
            sample = 'D'
        df_trep_ini['Time'] = df_trep_ini['Year'].apply(str) + '/' + df_trep_ini['Month'].apply(str) + '/' + \
                              df_trep_ini['Day'].apply(str)
        df_trep_ini['Time'] = pd.to_datetime(df_trep_ini['Time'], format='%Y/%m/%d')
        df_trep_ini.set_index('Time', inplace=True)
        df_trep = df_trep_ini.resample(sample).mean()

    data = [
        go.Bar(
            x=df_trep.index,
            y=100 * df_trep[country_1_code],
            text=list(round(100 * df_trep[country_1_code], 2)),
            textposition='auto',
            legendgroup='Country_1',
            hoverinfo='x+y',
            name=country_1,
            marker=dict(
                color='rgb(225, 202,158)',
                line=dict(
                    color='rgb(107,48,8)',
                    width=1.5),
            ),
            opacity=0.8
        ),
        go.Bar(
            x=df_trep.index,
            y=100 * df_trep[country_2_code],
            text=list(round(100 * df_trep[country_2_code], 2)),
            textposition='auto',
            legendgroup='Country_2',
            hoverinfo='x+y',
            name=country_2,
            marker=dict(
                color='rgb(202, 225, 158)',
                line=dict(
                    color='rgb(48, 107, 8)',
                    width=1.5),
            ),
            opacity=0.8
        ),
    ]

    layout = go.Layout(
        title='<b>Mean Load Factor per {} from {} to {}</b>'.format(gr_filter, time_range[0], time_range[1]),
        xaxis=dict(
            title=gr_filter,
        ),
        yaxis=dict(
            title='Load Factor [%]'
        ),
        legend=dict(
            x=.35,
            y=1.1,
            orientation="h"
        ),
        margin=dict(l=40, r=0),
        height=650,
        paper_bgcolor='#01053c',
        plot_bgcolor='#01053c',
        font=dict(color='#ffffff')
    )

    fig_cr = go.Figure(data=data, layout=layout)

    return fig_cr


def create_stacked(country_1, time_range, gr_filter, gr_sample):
    country_1_code = df_euro.loc[df_euro['Name'] == country_1, 'Code'].item()

    df_st_ini = df_data.loc[(df_data['Year'] >= time_range[0]) & (df_data['Year'] <= time_range[1]),
                              [country_1_code, 'Year', 'Month', 'Day', 'Hour']]

    list_per = np.linspace(10, 100, num=10)
    df_st = pd.DataFrame()
    if gr_sample == 'Mean':
        for df_gr in df_st_ini.groupby(gr_filter):
            if gr_filter == 'Month':
                idx = datetime.date(1900, df_gr[0], 1).strftime('%B')
            else:
                idx = df_gr[0]
            for per in list_per:
                df_st.loc[idx, per] = 100 * len(df_gr[1].loc[(100 * df_gr[1][country_1_code] <= per) &
                                                             (100 * df_gr[1][country_1_code] > per - 10)]) / len(df_gr[1])
    elif gr_sample == 'All':
        if gr_filter == 'Year':
            groupby_f = 'Year'
        elif gr_filter == 'Month':
            groupby_f = ['Year', 'Month']
        else:
            if time_range[1] == time_range[0]:
                groupby_f = ['Year', 'Month', 'Day']
            else:
                groupby_f = ['Year', 'Month']
        for df_gr in df_st_ini.groupby(groupby_f):
            idx = [str(i) for i in df_gr[0]]
            idx = pd.to_datetime('/'.join(idx), format='%Y/%m/%d')
            for per in list_per:
                df_st.loc[idx, per] = 100 * len(df_gr[1].loc[(100 * df_gr[1][country_1_code] <= per) &
                                                             (100 * df_gr[1][country_1_code] > per - 10)]) / len(df_gr[1])

    data = []
    for per in list_per:
        trace = go.Scatter(
            x=df_st.index,
            y=df_st[per],
            name='LF < {}%'.format(round(per, 0)),
            stackgroup='st_gr',
            groupnorm='percent'
        )
        data.append(trace)

    layout = go.Layout(
        title='<b>Load Factor Repartition in {} per {} from {} to {}</b>'.format(country_1, gr_filter, time_range[0],
                                                                                time_range[1]),
        xaxis=dict(
            title=gr_filter
        ),
        yaxis=dict(
            title='Time Percentage [%]'
        ),
        margin=dict(l=40, r=0),
        height=650,
        paper_bgcolor='#01053c',
        plot_bgcolor='#01053c',
        font=dict(color='#ffffff')
    )

    fig_cr = go.Figure(data=data, layout=layout)

    return fig_cr


########################################################################################################################
# Refresh Slider Range
########################################################################################################################
@app.callback([Output('c_sl_range', 'children')],
              [Input('sl_range', 'value')])
def refresh_slider_range(range_value):
    str_range = [str(range_value[0]) + ' - ' + str(range_value[1])]

    return str_range


########################################################################################################################
# Deployment
########################################################################################################################
if __name__ == '__main__':
    app.run_server(debug=True)
