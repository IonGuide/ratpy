import rats.modules.ratparser as ratparser
import plotly_express as px
import pandas as pd


def scopeplot(df,llc=0,buffer=1, facet=False,timescale=1000000):

    start = llc-buffer
    end = llc+buffer

    df['llc'] = df['llc'].astype('int')
    df['function'] = df['function'].astype('int')
    #create slice along the LLC dimension. This is more sensible than simply taking a packet-wise approach from the perspective of the user
    df = df[(df['llc'] >= start) & (df['llc'] <=end)]
    df.loc[:,'timescale'] = timescale
    df.loc[:,'time'] = df['time']/df['timescale']

    if facet:
        fig = px.line(df, x='time', y='data', color='edb', facet_row='edb',hover_data=['llc','function'])
        fig.update_yaxes(matches=None)
    else:
        fig = px.line(df, x='time', y='data', color='edb',hover_data=['llc','function'])

    #make sure markers are there in case user wants a single MRM scan, which would just be a single datapoint per edb
    fig.update_traces(mode='markers+lines',marker=dict(size=4))

    return fig

def test_case(file,absolutepath):
    try:
        df = pd.read_feather(f'../feathereddataframes/{file}.feather')
    except:
        print('df not found')
        filename = absolutepath
        testclass = ratparser.RatParse(filename)
        df = testclass.dataframeoutput()

    scopeplot(df,llc=30, buffer=2,facet=True).show()

file = 'RATS simulation 1595852200.txt'
# test_case(file,f'/users/steve/documents/workwaters/{file}')
