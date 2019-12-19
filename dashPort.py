# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import dash_table

import configparser as cp
import refinitiv.dataplatform as rdp
import json
import pandas as pd
from IPython.display import display, HTML
import datetime
import timedelta
import sys

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
#external_stylesheets = ['bWLwgP.css']

colors = {
    'background': '#111111', #'#404040', 
    'text': '#7FDBFF',
    'darkOrange': '#FF8C00'
}

#portfolioRics = ['AAPL.O','GM.N', 'T.N', 'VOD.L', 'CCL.L', 'IBM.N', 'GOOG.O', 'MSFT.O', 'AABA.O']
#portfolioRics = ['IBM.N','TSLA.O', 'TWTR.K','AAPL.O','GOOG.O','NTC.O','FB.O','AMZN.O']
portfolioRics = ['IBM.N','T.N', 'VOD.L','CCL.L','GOOG.O','TWTR.K','FB.O','AMZN.O']



newsColumns = [ 'Headline', 'storyDate', 'storyId' ]
newsColumnsDisplayed = [ 'Headline','storyDate']

histColumns = ['DATE','BID','ASK','OPEN_PRC','HIGH_1','LOW_1','TRDPRC_1','NUM_MOVES','TRNOVR_UNS']

# RDP session
def get_session(configFile):
    config = cp.ConfigParser()
    config.read(configFile)
    RDP_LOGIN = config['platform2']['user']
    RDP_PASSWORD = config['platform2']['password']
    APP_KEY = config['platform2']['app_key']

    session = rdp.PlatformSession(
        APP_KEY,
        rdp.GrantPassword(
            username = RDP_LOGIN,
            password = RDP_PASSWORD
        )
    )
    rdp.set_default_session(session)
    rdp.get_default_session().set_log_level(30)
    session.open()
    return session

def generate_headlines(instrum):
    headlines = pd.DataFrame()
    try:
        edate_str = datetime.date.today().strftime("%Y-%m-%d")
   #     print("Edate={}".format(edate_str))
        sdate_str = (datetime.date.today() - datetime.timedelta(days=3)).strftime("%Y-%m-%d")
    #    print("Sdate={}".format(sdate_str))
        headlines = rdp.get_news_headlines(query=instrum,
     #   headlines = rdp.get_news_headlines(query={"query": instrum, "relevance":"High"},
            count = 200,
            date_from = sdate_str, 
            date_to = edate_str)
   #     display(headlines)

  #      print("Headlines status={}".format(headlines.get_status))
        print("Headlines ={}".format(headlines))
  #      print("Headlines columns={}".format(headlines.columns))
        d = []
        for index, row in headlines.iterrows():
            d.append({'storyId': row['storyId'], 'storyDate': row['versionCreated'], 'Headline': row['text']} )
        headlines =  pd.DataFrame.from_dict(d)
    except:
        print("Exception occured in in generate_headlines on instrum {} {}".format(instrum,sys.exc_info()[0]))
    return headlines

def generate_story(story_id):
    story = rdp.get_news_story( story_id )
    return story


def get_sentiments(news_story):
    news_sentiments = {}
    if news_story.data.raw:
        content_meta = news_story.data.raw['newsItem'].get('contentMeta')
        if content_meta:
            content_meta_ex_property = content_meta.get('contentMetaExtProperty')
            if content_meta_ex_property:
                for ex_property in content_meta_ex_property:
                    if 'hasSentiment' in ex_property['_rel']:
                        news_sentiments[ex_property['_rel']] = ex_property['_value']
    return news_sentiments

def generate_analytics(ric, dfHeadlines):
    d = []
    for index, row in dfHeadlines.iterrows():
        news_story_full = news_story_endpoint.get_story(story_id=row['storyId'])
 #       print("News story full{}".format(json.dumps(news_story_full.json(), indent=2)))
        sentiments = get_sentiments(news_story_full)
 #       print("storyId={} storyDate={}".format(row['storyId'],row['storyDate']))
        if sentiments:
            print("Has sentiments storyId={} storyDate={} sentiments={}".format(row['storyId'],row['storyDate'],sentiments))
            d.append({'storyDate': row['storyDate'], 'positive': sentiments['extCptRel:hasSentimentPositive'],
                'negative': sentiments['extCptRel:hasSentimentNegative'], 'neutral': sentiments['extCptRel:hasSentimentNeutral'],
                'storyId': row['storyId']} )
    print("generate_analytics for RIC {} d={}".format(ric, d))
    return pd.DataFrame.from_dict(d)

def generate_hist(instrum):
    print("In generate_hist isntrum={},histColumns={}".format(instrum, histColumns))
    df = pd.DataFrame()
    try: 
        edate_str = datetime.date.today().strftime("%Y-%m-%dT23:59:59.000000000Z")
        sdate_str = (datetime.date.today() - datetime.timedelta(days=3)).strftime("%Y-%m-%dT00:00:00.000000000Z")
        df = rdp.get_historical_price_summaries(
            universe = instrum, #instrum,
            interval = rdp.Intervals.FIVE_MINUTES, 
            count = 500,
            start = sdate_str,
            end = edate_str
        ) 
 #       print("DataFrame={}".format(df))
    except:
        print("Exception occured in In generate_hist on instrum {},histColumns={}".format(instrum, histColumns))
    return df  

app = dash.Dash(__name__)

app.layout = html.Div(style={'backgroundColor': colors['background'],'color': colors['text'] }, className="container", children=[
    html.Div(
        children=[
            html.H1(children='Refinitiv Data Platform - Dash Portfolio Demo')
        ],
        style={'width':'100%', 'backgroundColor': colors['background'],'color': colors['text'], 'textAlign':'center'}
    ),
    html.Div(
        id='leftColumn',
        style={'width':'45%', 'height':'100%','float':'left','backgroundColor': colors['background'],'color': colors['text'],
        'text': colors['text']},
        children=[
            html.Div(
            style={'backgroundColor': colors['background'],'color': colors['darkOrange'], 'textAlign':'center'},
            children=[
                html.Label('Stock selected:')
            ]),
            dcc.Dropdown(
                id='dccDropRics',
                style={'color': colors['text'], 'backgroundColor': colors['background'],'font-weight':'bolder','width':600},
                options=[{'label':ric, 'value':ric} for ric in portfolioRics],
                value = portfolioRics[0]
      #          multi=False
            ),
            html.Div(
            children=[
                dcc.Graph(
                id='histGraph',
                figure={
                    'data': [],
                    'layout': {
                        'title' : 'Intraday Price History',
                        'plot_bgcolor': colors['background'],
                        'paper_bgcolor': colors['background'],
                        'font': {
                            'color': colors['text']
                        }
                    }
                },
                style={'height': 500,'width': 600}
                )
            ],
            style={'textAlign':'center','align':'center'}
            ),
            html.Div(
            id='historyLabel',
            style={'backgroundColor': colors['background'],'color': colors['darkOrange'], 'textAlign':'center','width':600},
            children=[
                html.Label('History on RIC')
            ]),
            html.Div(
            style={'align':'center','maxHeight': '200'},
            children=[
                dash_table.DataTable(
                    id='histDataTable',
                    columns=(                    
                        [{'id': p, 'name': p} for p in histColumns]
                    ),
                    data=[],
                    style_header={'backgroundColor': colors['background']},
                    style_cell={
                        'backgroundColor': colors['background'],
                        'color': colors['text'],
                        'textAlign': 'left', 'border': 'None'}, 
                    page_action="native",
                    page_current= 0,
                    page_size= 10,
                )
            ])
        ]
    ),
    html.Div(
        id='newsContent',
        style={'width':'55%', 'height':'100%','float':'right','backgroundColor': colors['background'],'color': colors['text']},
        children=[
            html.Div(
                id='newsLabel',
                style={'backgroundColor': colors['background'],'color': colors['darkOrange'], 'textAlign':'center'},
                children=[
                    html.Label('News on RIC')
                ]),
            dash_table.DataTable(
                id='updatedHeadlines',
                columns=(                    
                    [{'id': p, 'name': p} for p in newsColumns]
                ),
                data=[ 
                    {'storyId': 'id1', 'storyDate': 'date1e', 'Headline': 'headline1'},
                    {'storyId': 'urn:newsml:reuters.com:20190924:nBw9dJwG7a:1', 
                    'storyDate': '12-10-2004', 'Headline': '<a href="https://www.w3schools.com/html/">Visit our HTML tutorial</a>'}
                ],
                style_header={'backgroundColor': colors['background']},
                style_cell={
                    'backgroundColor': colors['background'],
                    'color': colors['text'],
                    'textAlign': 'left'
                },
                style_data={
                    'whiteSpace': 'normal',
                    'height': 'auto'
                },
                style_as_list_view=True,
                row_selectable='single',
                selected_rows=[],
                page_action="native",
                page_current= 0,
                page_size= 10,
            ),
            html.Div(
                id='updatedStory',
                style={'backgroundColor': colors['background'],'color': colors['text'], 'textAlign':'center'},
                children=[
                    html.Label('Story Placeholder')
                    ]),
            html.Div(
                id='updatedNewsSenitmentChart',
                style={'backgroundColor': colors['background'],'color': colors['darkOrange'], 'textAlign':'center'},
                children=[
                    dcc.Graph(
                    id='sentimentGraph',
                    figure={
                        'data': [],
                        'layout': {
                            'title' : 'News Sentiment Positive',
                            'plot_bgcolor': colors['background'],
                            'paper_bgcolor': colors['background'],
                            'font': {
                                'color': colors['text']
                            }
                        }
                    },
                    style={'width':'45%', 'height':'100%','float':'left','height': 300,'width': 400}
                    ),
                    dcc.Graph(
                    id='sentimentGraph2',
                    figure={
                        'data': [],
                        'layout': {
                            'title' : 'News Sentiment Negative',
                            'plot_bgcolor': colors['background'],
                            'paper_bgcolor': colors['background'],
                            'font': {
                                'color': colors['text']
                            },
                            'showlegend': True,
                            'text': 'storyId'
                        }
                    },
                    style={'width':'45%', 'height':'100%','float':'left','height': 300,'width': 400}
                    )
                ]
            )
        ]
    )
])

@app.callback(
    Output('updatedStory','children'),
    [Input('updatedHeadlines','selected_rows')],
    [State('updatedHeadlines', 'data')])
def update_styles(selected_rows, data):
    print("selected_rows={}".format(selected_rows)) # allowing single only
 #   print("data={}".format(data))
    g="" 
    story = "No story selected"
    for i in selected_rows:
        print("Selected storyId={}".format(data[i]['storyId']))
        g = g + str(i)
        story = generate_story(data[i]['storyId']) 
        print("Retrieved story:\n{}".format(story)) 
    return html.Label(story)

@app.callback(
    [Output('historyLabel', 'children'), 
    Output('histGraph', 'figure'),
    Output('histDataTable','data'),
    Output('newsLabel', 'children'),
    Output('updatedHeadlines', 'data'),
    Output('sentimentGraph','figure'),
    Output('sentimentGraph2','figure')
 ],
    [Input('dccDropRics', 'value')])
def update_all(selected_dropdown_value):
    print("selected_dropdown_value={}".format(selected_dropdown_value))
    hist_label = "No hist label yet"
    news_label = "No news label either, yet"
    hist_table_data = []
    hist_line_data = []
    news_table_data = []
    sentiment_pos_line_data = []
    sentiment_neg_line_data = []
#    for ric in selected_dropdown_value:
    ric = selected_dropdown_value
    print("History ric=",ric)
    d = generate_hist(ric)
    dn = generate_headlines(ric)
#        print("\nReturned history\n")
#        display(d) 
#        print("d={}".format(d))
    if not d.empty and d is not None:
        d['DATE'] = d.index
      #      print("index {}".format(d.index))
        if not hist_table_data: #empty
            hist_label =  html.Label('Price History on '+ ric)  #populate lable with first selected ric 
            news_label =  html.Label('News on '+ ric)  #populate lable with first selected ric
            hist_table_data = d.to_dict('rows')
            news_table_data = dn.to_dict('rows')
 #           print("hist_lines {} {}".format(list(d['DATE']),list(d['TRDPRC_1'])))
            if not dn.empty and dn is not None:
                ds = generate_analytics(ric, dn)
  #          print("lines {} {}".format(list(ds['storyDate']),list(ds['positive'])))
                if not ds.empty and ds is not None:
                    sentiment_pos_line_data.append( {'x': list(ds['storyDate']), 'y': list(ds['positive']), 'type': 'line', 'name': ric+" "+"positive"})
                    sentiment_neg_line_data.append( {'x': list(ds['storyDate']), 'y': list(ds['negative']), 'storyId': list(ds['storyId']), 'type': 'scatter', 'name': ric+" "+"negative"})
                else:
                    print("Sentiment data was none for ",ric)
            else:
                print("News data was none for ",ric)
        hist_line_data.append( {'x': list(d['DATE']), 'y': list(d['TRDPRC_1']), 'type': 'line', 'name': ric, 'connectgaps' : True})
    else:
        print("Hist data was none for ",ric)
        
    hist_chart_data = {
        'data': hist_line_data,
        'layout': {
                    'title' : 'Price History',
                    'plot_bgcolor': colors['background'],
                    'paper_bgcolor': colors['background'],
                    'font': {
                        'color': colors['text']
                    },
                    'showlegend': True
                }
    }
    sentiment_pos_chart_data = {
        'data': sentiment_pos_line_data,
        'layout': {
                    'title' : 'News Sentiment Positive',
                    'plot_bgcolor': colors['background'],
                    'paper_bgcolor': colors['background'],
                    'font': {
                        'color': colors['text']
                    },
                    'showlegend': True,
                    'text': 'storyId'
                }
    }
    sentiment_neg_chart_data = {
        'data': sentiment_neg_line_data,
        'layout': {
                    'title' : 'News Sentiment Negative',
                    'plot_bgcolor': colors['background'],
                    'paper_bgcolor': colors['background'],
                    'font': {
                        'color': colors['text']
                    },
                    'showlegend': True,
                    'text': 'storyId'
                }
    }
    return hist_label, hist_chart_data, hist_table_data, news_label, news_table_data , sentiment_pos_chart_data, sentiment_neg_chart_data    
       

if __name__ == '__main__':

    session = get_session("session.cfg")
    rdp.set_default_session(session)

    news_story_endpoint = rdp.NewsStory(session)
    
    app.run_server(debug=True,dev_tools_hot_reload=False)