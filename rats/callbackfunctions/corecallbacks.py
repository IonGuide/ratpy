from dash.dependencies import Input, Output, State
from rats.core.app import app
import dash_html_components as html
from dash.exceptions import PreventUpdate
import pandas as pd
import plotly_express as px
from rats.modules import ratparser
from flask import request
import pathlib
import platform
import dash_table
import dash_uploader as du

if platform.system() == 'Windows':
    cachepath = '\\cache\\'
    dfpath = '\\feathereddataframes\\'
    figurepath = '\\pickledfigures\\'
else:
    cachepath = '/cache/'
    dfpath = '/feathereddataframes/'
    figurepath = '/pickledfigures/'


packagepath = pathlib.Path(__file__).parent.parent.resolve()
du.configure_upload(app,str(packagepath)+cachepath,use_upload_id=False,)

'''
Contents: 
1 - Dropdown population 
    - Generic placeholder generation, fired on server startup
2 - File upload 
    - makedataframe() 
3 - Data pre-processing 
    - preprocessdata()
        - compares dataframes and checks for intra and inter file errors
4 - Figure management
    - clearprogramdata()
        - clears out files from rats/feathereddataframes and rats/pickledfigures
5 - Server shutdown 
    - shutdown()
        - clears the RATS files and sessionfilenames dataframe from the rats/cache directory

'''

#============================================================
#           DROPDOWN POPULATION
#============================================================
## have to create some placeholders for the callbacks to get their teeth into something - this is a plaster over a Dash issue
filenames = []
dataframes = []
bigpictureplotdata = []
scopeplotdata = []
interscanplotdata = []

dropdownoptions = []
for i in range(12):
    item = {'label': f'Data Slot {i + 1}', 'value': i}
    dropdownoptions.append(item)

placeholderfig = px.line(x=[1, 2, 3, 4], y=[1, 2, 3, 4],
                         title='placeholder')  # will be changed later, possibly to something representative

colors = {'background': '#111111', 'text': '#7FDBFF'}

dropdownoptions = []
for i in range(12):
    item = {'label': f'Data Slot {i + 1}', 'value': i}
    dropdownoptions.append(item)

#============================================================
#           /DROPDOWN POPULATION
#============================================================


# ============================================================
#           FILE UPLOAD
# ============================================================
#### DATAFRAME PRODUCTION
@app.callback(Output('errorlog', 'children'),
              Input('dash-uploader', 'isCompleted'),
              State('errorlog','children'))
def upload(complete,error):
    # format the relevant information into a dataframe, to append later to the session dataframe or to store as the first instance
    # this returns after pre-processing and it's not clear why, so it preserves the sate of the error log
    if not complete:
        return
    return error

# ============================================================
#           /FILE UPLOAD
# ============================================================

#============================================================
#           DATA PRE-PROCESSING
#============================================================

@app.callback([Output('datalist','children'),
               Output('errorlogcontainer','children'),
               Output('ratdashpullcontainer','children'),
               Output('scopepullcontainer','children'),
               Output('interscanpullcontainer','children')],
              [Input('processdata','n_clicks')])
def preprocessdata(click):
    errormessage = ''
    #function to add to the session file dataframe the status of each file and yield the gui output
    if click is None:
        raise PreventUpdate

    list_of_names = []
    import os
    for filename in os.listdir(str(packagepath / 'cache')):
        if '.txt' in filename:
            list_of_names.append(filename)

    filenamedf = pd.DataFrame(
        dict(file=list_of_names, processed=['no' for i in list_of_names]))

    for i in list_of_names:
        try:
            # try to load an existing sessionfilenames
            sessionfilenames = pd.read_feather(str(packagepath) + cachepath + 'sessionfilenames')
            if i not in sessionfilenames['file'].unique():
                ## add this new file to the sessionfilenames dataframe if it's not already there
                sessionfilenames = sessionfilenames.append(filenamedf, ignore_index=True)
                sessionfilenames.to_feather(str(packagepath) + cachepath + 'sessionfilenames')
        except:
            ## if there was no cache of session filenames, then use this filename to create the dataframe in the cache
            sessionfilenames = filenamedf
            sessionfilenames.to_feather(str(packagepath) + cachepath + 'sessionfilenames')

        try:
            ## see if there's a valid dataframe stored for this file
            pd.read_feather(str(packagepath) + dfpath + f'{i}.feather')
            print('found df')
        except:
            ## should be a case of now reading this file in from cache instead of from some absolute path...
            parser = ratparser.RatParse(str(packagepath) + cachepath + f'{i}')
            #soomething's going wrong here when reading file back in from cache
            if parser.verifyfile():
                df = parser.dataframeoutput()
                df.to_feather(str(packagepath) + dfpath + f'{i}.feather')
            else:
                #remove the filename from the session and the file from the cache
                sessionfilenames = pd.read_feather(str(packagepath) + cachepath + 'sessionfilenames')
                sessionfilenames = sessionfilenames[sessionfilenames['file'] != i]
                sessionfilenames.reset_index(drop=True,inplace=True)
                sessionfilenames.to_feather(str(packagepath) + cachepath + 'sessionfilenames')
                import os, shutil
                file_path = os.path.join(str(packagepath / 'cache'), i)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print('Failed to delete %s. Reason: %s' % (file_path, e))
                errormessage = f'File {i} could not be verified as a RATS file'

    try:
        sessionfilenames = sessionfilenames.drop_duplicates(subset='file')
        sessionfilenames.reset_index(drop=True,inplace=True)
        filenames = sessionfilenames['file'].tolist()
        log = []
        for i in filenames:
            message = ''
            df1 = pd.read_feather(str(packagepath) + dfpath + f'{i}.feather')
            if 1 in df1['anomalous'].tolist():
                message += 'There may be an error in this file\n '
            df1 = df1.drop_duplicates(subset=['llc'])
            for j in filenames:
                if j != i:
                    df2 = pd.read_feather(str(packagepath) + dfpath + f'{j}.feather')
                    df2 = df2.drop_duplicates(subset=['llc'])
                    if df1['function'].equals(df2['function']):
                        print(f'File {j} complements file {i}')
                    else:
                        print(f'File {j} does not complement file {i}')
                        message += f'This file does not complement file {j}\n '
            if message == '':
                log.append('No issues detected\n')
            else:
                log.append(message)

        sessionfilenames['log'] = log
        sessionfilenames['processed'] = 'yes'
        sessionfilenames.to_feather(str(packagepath) + cachepath + 'sessionfilenames')
        print('stored sessionfilenemes df')

        tabledata = sessionfilenames[['file','log']]
        children = dash_table.DataTable(
                    id='table',
                    columns=[{"name": i, "id": i} for i in tabledata.columns],
                    data=tabledata.to_dict('records'),
                    style_data_conditional=[{
                        'if': {
                            'filter_query': "{log} contains 'There may be an error in this file'",
                            'column_id': 'log'

                        },
                        'border-top-color': 'Tomato',
                        'border-bottom-color': 'Tomato',
                        'border-top-style': 'solid',
                        'border-bottom-style': 'solid',
                        'border-top-width': '1px',
                        'border-bottom-width': '1px',
                        'background-color':'rgba(255,65,54,0.2)'

                    },
                    {
                        'if': {
                            'filter_query': "{log} contains 'This file does not complement file'",
                            'column_id': 'log'

                        },
                        'border-top-color': 'Tomato',
                        'border-bottom-color': 'Tomato',
                        'border-top-style' : 'solid',
                        'border-bottom-style' : 'solid',
                        'border-top-width' : '1px',
                        'border-bottom-width' : '1px',
                        'background-color':'rgba(252,186,3,0.2)'
                    },
                    {
                        'if': {
                            'filter_query': "{log} contains 'No issues'",
                            'column_id': 'log'

                        },
                        'border-top-color': 'Green',
                        'border-bottom-color': 'Green',
                        'border-top-style': 'solid',
                        'border-bottom-style': 'solid',
                        'border-top-width': '1px',
                        'border-bottom-width': '1px',
                        'background-color': 'rgba(60,201,72,0.2)'
                    },
                    ],
                    style_cell = {'whiteSpace':'pre-line',
                                  'textAlign':'center',
                                  'font-family': 'sans-serif'},
                    style_as_list_view=True)
        ## all manipulation of sessionfilenames dataframe is now complete...
        print(errormessage)

        rdbutton = html.Button(id='pulldataratdash',children='Pull the data into ratdash',className='btn btn-secondary', type='button')
        sbutton = html.Button(id='pulldatascope',children='Pull the data into scope app',className='btn btn-secondary', type='button')
        ibutton = html.Button(id='pulldatainterscan',children='Pull the data into interscan app',className='btn btn-secondary', type='button')

        return children, html.Div([errormessage],id='errorlog', className='col'), rdbutton, sbutton, ibutton
    except:
        print('epic fail')
        rdbutton = html.Button(id='pulldataratdash',children='Pull the data into ratdash',className='btn btn-secondary', type='button')
        sbutton = html.Button(id='pulldatascope',children='Pull the data into scope app',className='btn btn-secondary', type='button')
        ibutton = html.Button(id='pulldatainterscan',children='Pull the data into interscan app',className='btn btn-secondary', type='button')
        return [], 'failed to preprocess data',rdbutton, sbutton, ibutton
        pass

#============================================================
#           /DATA PRE-PROCESSING
#============================================================


#============================================================
#           CLEAR PROGRAM DATA
#============================================================
@app.callback(Output('clearstatus','children'),
              [Input('cleardata','n_clicks')])
def clearprogramdata(n_clicks):
    if n_clicks == None:
        pass
    else:
        print('Ratdash has cleared all the program data!')

        #clear session data before shutdown
        import os, shutil
        for filename in os.listdir(str(packagepath / 'feathereddataframes')):
            if filename != '__init__.py':
                file_path = os.path.join(str(packagepath / 'feathereddataframes'), filename)
            else:
                file_path = False
            if file_path:
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print('Failed to delete %s. Reason: %s' % (file_path, e))

        for filename in os.listdir(str(packagepath / 'pickledfigures')):
            if filename != '__init__.py':
                file_path = os.path.join(str(packagepath / 'pickledfigures'), filename)
            else:
                file_path = False
            if file_path:
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print('Failed to delete %s. Reason: %s' % (file_path, e))

        return 'All previously processed data has been cleared'

#============================================================
#           /CLEAR PROOGRAM DATA
#============================================================

#============================================================
#           PROGRAM SHUTDOWN
#============================================================
@app.callback(Output('runstatus','children'),
              [Input('shutdown','n_clicks')])
def shutdown(n_clicks):
    if n_clicks == None:
        pass
    else:
        print('Ratdash says goodbye!')

        #clear session data before shutdown
        import os, shutil
        for filename in os.listdir(str(packagepath / 'cache')):
            if filename != '__init__.py':
                file_path = os.path.join(str(packagepath / 'cache'), filename)
            else:
                file_path = False
            if file_path:
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print('Failed to delete %s. Reason: %s' % (file_path, e))

        func = request.environ.get('werkzeug.server.shutdown')
        func()
        return 'Server has been shut down, please close the browser window'

#============================================================
#           /PROGRAM SHUTDOWN
#============================================================






