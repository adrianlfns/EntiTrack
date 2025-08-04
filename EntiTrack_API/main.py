'''
This is the main entry point for the flask API application.
This flask application uses Flask-RESTx for API management and Flask-CORS for handling cross-origin requests.
Flask-RESTx enables developers to create RESTful APIs with ease, and provide the swagger documentation at the same time.
'''

import os

from flask import Flask,send_from_directory
from flask_restx import Api

from flask_cors import cross_origin

#namespaces to be registered
from apis.ns_genai import namespace_ner_gen_ai
from apis.ns_train import namespace_ner_train

###############################Begin configuration to serve static files for the Blazor WebAssembly app###############################
BLAZOR_BUILD_DIR = 'UI' # Relative to your Flask static folder

#Innit a Flask app with a static folder serving on static URL path '/UI'
#The content of UI folder will be populated when the scrip scr_publish_start.sh is run or the script scr_UI_publish.sh is run.
app = Flask(__name__, static_folder=BLAZOR_BUILD_DIR, static_url_path='/UI')
app.config['RESTX_MASK_SWAGGER'] = False
#app.config['SWAGGER_UI_DOC_EXPANSION'] = 'full'


@app.route('/UI/<path:filename>') 
def serve_blazor_static(filename):
    # This route handles all static files within the Blazor app
    # It sends files from the 'static/UI' directory
    return send_from_directory(app.static_folder + '/', filename)

@app.route('/UI/')
@app.route('/UI')
def serve_blazor_index():
    # This route serves the main index.html for the Blazor app
    # When someone navigates to /UI or /UI/, it serves the index.html
    return send_from_directory(app.static_folder + '/', 'index.html')

#this is just to add a quick ling to open the UI from the API documentation
open_UI_link = ''
ui_folder = os.path.join(BLAZOR_BUILD_DIR)
if os.path.exists(ui_folder) and os.listdir(ui_folder):
   open_UI_link = "<br/><br/><a href='UI/' target='_blank'>Open UI</a>"  
###############################End configuration to serve static files for the Blazor WebAssembly app###############################
   


###############################Begin configuration to flask restx###############################

# Initialize Flask-RESTx API
# Configure the API with two namespaces: one for NER generation using GenAI and another for training NER models. See folder apis for details on the namespaces.
api = Api(app=app, 
          title="EntiTrack API.", 
          description=f"Perform custom Named Entity Recognition (NER) from unstructured text.{open_UI_link}",)

api.add_namespace(namespace_ner_gen_ai)
api.add_namespace(namespace_ner_train)

###############################Begin configuration to flask restx###############################


#this is is to allow CORS for all routes
@app.after_request
def after_request(response):
  header = response.headers
  header['Access-Control-Allow-Origin'] = '*' # Or specify your allowed origin(s)
  header['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
  header['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
  return response


if __name__ == "__main__":
  app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 3000)))