import urllib
from dash import Dash, dcc, html, Input, Output, State, callback
import dash_bootstrap_components as dbc

driveURL = 'https://drive.google.com/drive/folders/1NagF8mm10_R87fBPFcmJgS8izytZ1JI_?usp=share_link'

app = Dash(__name__,external_stylesheets=[dbc.themes.SLATE])

import gdown
driveFolder = gdown.download_folder(driveURL,output='assets/',quiet=True,use_cookies=False)
print(driveFolder)
# r = requests.get(drivePictures)
# print(r.text)


# Can't seem to get this to work for downloading directly from Google Drive. Might need to do it manually and push to github.

# builtNucleusPicture = html.Img(src='assets/logo.png',style={'height':'50vh'})
builtNucleusPicture = html.Img(src='assets/Approved_Pictures/4He_0.jpeg',style={'height':'50vh'})

app.layout = html.Div([
    builtNucleusPicture
])

# Run app...
if __name__ == '__main__':
    app.run(debug=True)