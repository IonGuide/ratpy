
from rats.modules import ratparser
import numpy as np
import plotly_express as px


#function to run on initial upload
def bigpictureplot(df,timescale=1000000):
    df = df[['function','packet', 'llc', 'anomalous', 'time']]
    df.drop_duplicates(subset = ['llc','anomalous'],inplace=True)
    df.loc[:,'colours'] = np.where(df['anomalous'] == 0, 'blue', 'red')
    df.loc[:,'timescale'] = timescale
    df.loc[:,'time'] = df['time']/df['timescale']

    fig = px.scatter(df, x='time', y='function', color='colours', hover_data=['llc'])
    return fig

def test_case(absolutepath):
    import pickle
    testclass = ratparser.RatParse(absolutepath)
    df = testclass.dataframeoutput()

    fig = bigpictureplot(df)

    with open('figurepickletest.pickle', 'wb') as f:
        pickle.dump(fig, f)

    with open('figurepickletest.pickle', 'rb') as f:
        fig2 = pickle.load(f)

    fig2.show()

# test_case('/users/steve/documents/workwaters/RATS simulation 1587748688.txt')