import dash

app = dash.Dash(__name__, external_stylesheets=['https://stackpath.bootstrapcdn.com/bootstrap/'
                                                '4.4.1/css/bootstrap.min.css'], suppress_callback_exceptions=True)
server = app.server
