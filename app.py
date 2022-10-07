#!/usr/bin/python3
from datetime import date

import dash
import dash_bootstrap_components as dbc
from dash import dcc
from dash import html
import pandas
from dash.dependencies import Input, Output

# data URL
url = 'https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-regioni/dpc-covid19-ita-regioni.csv'
today = date.today()
REF_TAMP = 9000  # reference value

# read csv for url
df = pandas.read_csv(url)
# get a list off all regions
regions = df['denominazione_regione'].drop_duplicates().tolist()

plotly_js_minified = ['https://cdn.plot.ly/plotly-basic-latest.min.js']

app = dash.Dash(__name__, external_scripts=plotly_js_minified,
                meta_tags=[{'name': 'viewport',
                            'content': 'width=device-width, initial-scale=1.0, maximum-scale=1.2, minimum-scale=0.5'}],
                requests_pathname_prefix='/regions/',
                routes_pathname_prefix='/regions/'
                )
app.title = 'Dashboard Regioni'

server = app.server

# chart config
chart_config = {'displaylogo': False,
                'displayModeBar': False
                }

# slider buttons
slider_button = list([
    dict(count=1,
         label="1m",
         step="month",
         stepmode="backward"),
    dict(count=3,
         label="3m",
         step="month",
         stepmode="backward"),
    dict(count=6,
         label="6m",
         step="month",
         stepmode="backward"),
    dict(step="all")
])


def update_data():
    global df
    df = pandas.read_csv(url)


def calculate_data(data):
    # data calculation
    data['terapia_intensiva_avg'] = data['terapia_intensiva'].rolling(7).mean()
    data['nuovi_decessi'] = data.deceduti.diff().fillna(data.deceduti)

    # percentage swab - cases
    data['delta_casi_testati'] = data.casi_testati.diff().fillna(data.casi_testati)
    data['incr_tamponi'] = data.tamponi.diff().fillna(data.tamponi)
    data['perc_positivi_tamponi'] = (data['nuovi_positivi'] / data['incr_tamponi']) * 100  # AB
    data['perc_positivi_test'] = (data['nuovi_positivi'] / data['delta_casi_testati']) * 100  # AD

    # rolling averages
    data['nuovi_positivi_avg'] = data['nuovi_positivi'].rolling(7).mean()
    data['nuovi_decessi_avg'] = data['nuovi_decessi'].rolling(7).mean()
    data['totale_ospedalizzati_avg'] = data['totale_ospedalizzati'].rolling(7).mean()
    data['perc_positivi_tamponi_avg'] = data['perc_positivi_tamponi'].rolling(3).mean()
    data['perc_positivi_test_avg'] = data['perc_positivi_test'].rolling(3).mean()

    # norm cases
    data['nuovi_casi_norm'] = data['nuovi_positivi'] * REF_TAMP / data['incr_tamponi']
    return data


def get_dropdown_data():
    selections = []
    for reg in regions:
        selections.append(dict(label=reg, value=reg))
    return selections


app.layout = html.Div(  # main div
    dbc.Container([
        dbc.Row(
            [
                dbc.Col(
                    html.Img(id='logo-regione',
                             style=dict(width='30%')
                             )

                    , width=12, lg=4),

                dbc.Col(
                    dcc.Dropdown(id='region_select',
                                 options=get_dropdown_data(),
                                 clearable=False,
                                 placeholder='Seleziona una regione...',
                                 searchable=False,
                                 persistence=True,
                                 persistence_type='session',
                                 value='Lombardia'
                                 )

                    , width=12, lg=5,
                    className='mt-2')
            ]
            , className='text-center'),
        dbc.Row(  # andamento contagi
            dbc.Col(
                dcc.Graph(
                    id='andamento-contagi',
                    figure={},
                    config=chart_config
                )
                , width=12)
        ),

        dbc.Row(
            dbc.Col(
                dcc.Graph(
                    id='perc-casi-tamponi',
                    figure={},
                    config=chart_config
                )
                , width=12)
        ),

        dbc.Row(
            dbc.Col(
                dcc.Graph(
                    id='totale-ospedalizzati',
                    figure={},
                    config=chart_config
                )
                , width=12,

            )
        ),

        dbc.Row(
            dbc.Col(
                dcc.Graph(
                    id='decessi-giornalieri',
                    figure={},
                    config=chart_config
                )
                , width=12,
            )
        ),

        dbc.Row(
            dbc.Col(
                dcc.Graph(
                    id='terapia-intensiva',
                    figure={},
                    config=chart_config
                )
                , width=12),

        )

    ], className='mt-5')
)


@app.callback(
    Output('andamento-contagi', 'figure'),
    [Input('region_select', 'value')])
def update_andamento_contagi(regione):
    update_data()
    reg_df = df.loc[df['denominazione_regione'] == regione]
    local_df = calculate_data(reg_df.copy())
    figure = {
        'data': [
            {'x': local_df['data'], 'y': local_df['nuovi_positivi'], 'type': 'bar', 'name': 'Nuovi Casi'},
            {'x': local_df['data'], 'y': local_df['nuovi_positivi_avg'], 'type': 'scatter',
             'line': dict(color='orange'),
             'name': 'Media 7 giorni'}
        ],
        'layout': {
            'title': 'Andamento dei contagi',
            'xaxis': dict(
                rangeselector=dict(buttons=slider_button),
                rangeslider=dict(visible=False),
                type='date'
            )
        }
    }
    return figure


@app.callback(
    Output('perc-casi-tamponi', 'figure'),
    [Input('region_select', 'value')])
def update_perc_casi_tamponi(regione):
    update_data()
    reg_df = df.loc[df['denominazione_regione'] == regione]
    local_df = calculate_data(reg_df.copy())
    figure = {
        'data': [
            {'x': local_df['data'], 'y': local_df['perc_positivi_test'], 'type': 'scatter',
             'name': 'Nuovi Casi testati', 'line': dict(color='orange')},
            {'x': local_df['data'], 'y': local_df['perc_positivi_tamponi'], 'type': 'scatter',
             'line': dict(color='blue'),
             'name': 'Totale casi testati'},
            {'x': local_df['data'], 'y': local_df['perc_positivi_test_avg'], 'type': 'scatter',
             'name': 'Nuovi Casi (media 3gg)', 'line': dict(color='orange', dash='dot')},
            {'x': local_df['data'], 'y': local_df['perc_positivi_tamponi_avg'], 'type': 'scatter',
             'line': dict(color='blue', dash='dot'),
             'name': 'Totale casi (media 3gg)'}
        ],
        'layout': {
            'title': '% Nuovi Casi / Test tramite tamponi',
            'xaxis': {
                'type': 'date',
                'range': ['2020-04-22', today],
                'rangeselector': dict(buttons=slider_button),
                'rangeslider': dict(visible=False)

            },
            'yaxis': {
                'range': [0, 30],
                'tickprefix': '% '
            }

        }
    }
    return figure


@app.callback(
    Output('totale-ospedalizzati', 'figure'),
    [Input('region_select', 'value')])
def update_ospedalizzati(regione):
    update_data()
    reg_df = df.loc[df['denominazione_regione'] == regione]
    local_df = calculate_data(reg_df.copy())
    figure = {
        'data': [
            {'x': local_df['data'], 'y': local_df['totale_ospedalizzati'], 'type': 'bar',
             'name': 'Ospedalizzazioni'},
        ],
        'layout': {
            'title': 'Totale ospedalizzati',
            'xaxis': dict(
                rangeselector=dict(buttons=slider_button),
                rangeslider=dict(visible=False),
                type='date'
            )
        }
    }
    return figure


@app.callback(
    Output('decessi-giornalieri', 'figure'),
    [Input('region_select', 'value')])
def update_decessi_giornalieri(regione):
    update_data()
    reg_df = df.loc[df['denominazione_regione'] == regione]
    local_df = calculate_data(reg_df.copy())
    figure = {
        'data': [
            {'x': local_df['data'], 'y': local_df['nuovi_decessi'], 'type': 'bar',
             'marker': dict(color='grey')},
        ],
        'layout': {
            'title': 'Decessi giornalieri',
            'xaxis': dict(
                rangeselector=dict(buttons=slider_button),
                rangeslider=dict(visible=False),
                type='date'
            )
        }
    }
    return figure


@app.callback(
    Output('terapia-intensiva', 'figure'),
    [Input('region_select', 'value')])
def update_terapia_intensiva(regione):
    update_data()
    reg_df = df.loc[df['denominazione_regione'] == regione]
    local_df = calculate_data(reg_df.copy())
    figure = {
        'data': [
            {'x': local_df['data'], 'y': local_df['terapia_intensiva'], 'type': 'bar', 'name': 'Terapia Intensiva',
             'marker': dict(color='LightSalmon')},
            {'x': local_df['data'], 'y': local_df['terapia_intensiva_avg'], 'type': 'scatter',
             'line': dict(color='blue'),
             'name': 'Media 7 giorni'}
        ],
        'layout': {
            'title': 'Terapia intensiva',
            'xaxis': dict(
                rangeselector=dict(buttons=slider_button),
                rangeslider=dict(visible=False),
                type='date'
            )
        }
    }
    return figure


@app.callback(
    Output('logo-regione', 'src'),
    [Input('region_select', 'value')])
def update_logo(regione):
    src = 'assets/img/' + regione + '.png'
    return src


if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8050, debug=False)
