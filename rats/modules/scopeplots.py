import rats.modules.ratparser as ratparser
import plotly_express as px
import pandas as pd


def scopeplot(df, llc=0, buffer=1, facet=False, timescale=1000000):
    # establish valid filters for dataframe and try to handle anomalous input.
    df['llc'] = df['llc'].astype('int')
    if llc-buffer > int(df.llc.max()):
        start = int(df.llc.max()) - 10
    else:
        start = llc-buffer
    if start + (2*buffer) < int(df.llc.min()):
        end = int(df.llc.min())
    else:
        end = start + (2*buffer)

    df['function'] = df['function'].astype('int')
    df = df[(df['llc'] >= start) & (df['llc'] <= end)]
    df['timescale'] = timescale
    df['time'] = df['time'] / df['timescale']
    title = df['board'].tolist()[0]

    if facet:
        fig = px.line(df, x='time', y='data', color='edb', facet_row='edb', hover_data=['llc', 'function'], title=title)
        fig.update_yaxes(matches=None)
        fig.for_each_annotation(lambda a: a.update(text=''))
        fig.update_layout(showlegend=False)
    else:
        fig = px.line(df, x='time', y='data', color='edb', hover_data=['llc', 'function'], title=title)

    # make sure markers are there in case user wants a single MRM scan, which would just be a single datapoint per edb
    fig.update_traces(mode='markers+lines', marker=dict(size=4))

    return fig


def test_case(file, absolutepath):
    try:
        df = pd.read_feather(f'../feathereddataframes/{file}.feather')
    except Exception:
        print('df not found')
        filename = absolutepath
        testclass = ratparser.RatParse(filename)
        df = testclass.dataframeoutput()

    fig = scopeplot(df, llc=30, buffer=2, facet=True)
    fig.show()

# import plotly.io as pio
# pio.renderers.default = "firefox"
#
# file = 'RATS simulation 1595852200.txt'
# test_case(file,f'/users/steve/documents/workwaters/{file}')
