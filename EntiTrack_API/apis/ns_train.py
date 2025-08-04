from flask_restx import Resource,Namespace, abort, reqparse,fields 
from werkzeug.datastructures import FileStorage
from flask_cors import cross_origin

import pandas as pd
from sklearn.model_selection import train_test_split

import re 
import uuid

import spacy
from spacy.tokens import DocBin
from spacy.util import filter_spans

import os

import subprocess
import sys
import shutil

import json

from datetime import datetime





namespace_ner_train = Namespace('SpaCy NER (Train with sample data)', 
                             description='Perform NER by trining a SpaCy model.', 
                             path="/spacy_train_ner", ordered=False,
                              decorators=[cross_origin()])


 

training_session_model = namespace_ner_train.model("training_session",{
  'training_session_id': fields.String(required=True, description='Session key for acceding a trained model.'),
  'is_valid': fields.Boolean(required=True, description='Indicates if the session is valid and can be used.'),
  'invalid_message': fields.String(required=False, description='Reason why the session is invalid.'),
  'ner_fields': fields.List(fields.String(required=False, description='NER fields.')),
  'performance': fields.Raw(description='Performance Metrics'),
  'date_created': fields.String(required=False, description='Date when the session was created.'),
  'training_description': fields.String(required=False, description='Brief description of the training session.'),
})




file_upload_parser = reqparse.RequestParser()
file_upload_parser.add_argument('file',
                               type=FileStorage,
                               location='files',
                               required=True,
                               help='Training data file (CSV)')   
file_upload_parser.add_argument('unstructured_column_name', 
                                type=str, 
                                required=True,
                                location='form',
                                help='Name of the column with unstructured text to parse. The column must be present in the CSV file provided in the request.')  
file_upload_parser.add_argument('training_description', 
                                type=str, 
                                required=True,
                                location='form',
                                help='Brief description of your training session.')  



@namespace_ner_train.route("/train")
class TrainModels(Resource):
  
  @namespace_ner_train.expect(file_upload_parser)
  @namespace_ner_train.response(400, 'Invalid request.')
  @namespace_ner_train.marshal_with(training_session_model)
  def post(self):
    """Train an SpaCy Model. Given a dataset and the name of the unstructured column."""
    args = file_upload_parser.parse_args()
    uploaded_file = args['file']
    unstructured_column_name = args['unstructured_column_name']
    training_description = args['training_description']

    if not unstructured_column_name:
       abort(400, message="Unstructured column name is required.")


    if not uploaded_file:
       abort(400, message="A file was expected in the request.")

    if not training_description:
       abort(400, message="Training description is required.")

    if not uploaded_file.filename.lower().endswith('.csv'):
       abort(400, message="The file provided in the request was expected to be a file with extension CSV.")

    data_frame_train = None
    try:
      data_frame_train=pd.read_csv(filepath_or_buffer=uploaded_file,sep=",",dtype=str)
    except Exception as e:
      abort(400, message=f"The submitted file is an invalid CSV. Error message: {e}")

    column_list = data_frame_train.columns.to_list()


    TAG_SUFFIX = "__TAG" 

    if unstructured_column_name not in column_list:
      abort(400, message=f'The submitted csv file is missing the column with name "{unstructured_column_name}"')
    
    if len(column_list) <=1:
      abort(400, message=f'The submitted csv file does does not have enough columns. Expected to have the column "{unstructured_column_name}" and at least another column.')

    fragment_columns = [column for column in column_list if column != unstructured_column_name]
    fragment_tag_columns = [column + TAG_SUFFIX for column in fragment_columns]


    X_train, X_test, _, _ = train_test_split(data_frame_train, data_frame_train, test_size=0.3, random_state=42)

    df_entity_spans_train= create_entity_spans(data_frame=X_train.astype(str), 
                                                tag_list= fragment_tag_columns,
                                                text_to_parse_column=unstructured_column_name, 
                                                tag_suffix= TAG_SUFFIX)

    
    df_entity_spans_test = create_entity_spans(data_frame=X_test.astype(str), 
                                                tag_list= fragment_tag_columns,
                                                text_to_parse_column=unstructured_column_name, 
                                                tag_suffix= TAG_SUFFIX) 
    
    nlp = spacy.blank("en")

    train_doc_bin = get_doc_bin(data=df_entity_spans_train.values.tolist(),
                                nlp=nlp)
    
    test_doc_bin = get_doc_bin(data=df_entity_spans_test.values.tolist(),
                               nlp=nlp)  
    
    training_session_id = str(uuid.uuid4())
   
    directory_path = os.path.join("model_train_sessions",training_session_id)
    os.makedirs(name=directory_path, exist_ok=False) 

    train_spacy_path = os.path.join(directory_path,"train.spacy")
    train_doc_bin.to_disk(train_spacy_path)
  
    test_spacy_path = os.path.join(directory_path,"test.spacy")
    test_doc_bin.to_disk(test_spacy_path)

    models_path = os.path.join(directory_path,"models")

    oConfig_path = os.path.join("config","config.cfg")


    # Define the command and its arguments as a list
    command = [
        sys.executable,  # Use the current Python executable
        "-m",
        "spacy",
        "train",
        oConfig_path,
        "--paths.train",
        train_spacy_path,
        "--paths.dev",
        test_spacy_path,
        "--output",
        models_path,
        "--training.eval_frequency",
        "10",
        "--training.max_steps",
        "300"
    ]

   
    try:
        # Run the command
        result = subprocess.run(command, check=True, capture_output=True, text=True)

        # Print the output (optional)
        print("STDOUT:")
        print(result.stdout)
        print("STDERR:")
        print(result.stderr)

        if result.stderr:
           try_to_delete_session_folder(directory_path)
           abort(400, message=f'Error while training the model."')

    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        try_to_delete_session_folder(directory_path)
        abort(400, message=f'Error while training the model STDERR:"{e.stderr}; STDOUT:{e.stdout}"')


    except FileNotFoundError:
        print("Error: Could not find the 'spacy' executable. Make sure spaCy is installed and accessible in your environment.")
        try_to_delete_session_folder(directory_path)
        abort(400, message=f'Error while training the model."')

    edit_training_session_metadata(training_session_id=training_session_id,
                                   training_description=training_description)
    
    return get_training_session_data(training_session_id)


train_ner_payload = reqparse.RequestParser()
train_ner_payload.add_argument('text_to_check', type=str, required=True, help='Text that will be used to perform NER', location='form')
train_ner_payload.add_argument('training_session_id', type=str, required=True, help='Training session id obtained from listing the trainings.', location='form')



@namespace_ner_train.route("/perform_ner")
@namespace_ner_train.response(400, 'Invalid data.')
@namespace_ner_train.response(500, 'Internal errors.')
@namespace_ner_train.expect(train_ner_payload)
class PerformNer(Resource):
   def post(self):
      """Perform NER given a trained SpaCy model (session_ID)"""
      
      args = train_ner_payload.parse_args()  # Parse and extract the arguments
      training_session_id = args['training_session_id']

      if not training_session_id:
         abort(400, f"Training Session ID is required.")      

      res = get_training_session_data(training_session_id)
      if not res.is_valid:
         abort(400, f"Session with id {training_session_id} is missing or invalid.")   

      text_to_check = args['text_to_check']
      if not text_to_check:
         abort(400, message="Text to check is required.") 

      directory_path = os.path.join("model_train_sessions",training_session_id, "models","model-best")

      try:
         nlp=spacy.load(directory_path)
      except Exception as e:
         abort(500, message=f"Errors found while loading the session model. Error Message {e}") 

      document = nlp(text_to_check)
      entities =[{'Entity Label:': ent.label_,
                                 'Entity Text': ent.text,                    
                                 'Entity Start Index': ent.start_char, 
                                 'Entity End Index':ent.end_char} for ent in document.ents]

      result = entities    
    
      return result


      
def edit_training_session_metadata(training_session_id, training_description):
   """Add some more metadata to the json file of a training session."""
   directory_path = os.path.join("model_train_sessions",training_session_id)
   best_model_path = os.path.join(directory_path,"models","model-best")
   meta_data_file = os.path.join(best_model_path,"meta.json")
   today = datetime.now()
   formatted_today = today.strftime("%m/%d/%Y %H:%M:%S %p")

   # Read the existing metadata file
   data = None
   with open(meta_data_file, 'r') as f:
      data = json.load(f)

   # Add or update the date_created field in the metadata
   data['date_created'] = formatted_today
   data['training_description'] = training_description
   
   #write the updated metadata back to the file
   with open(meta_data_file, 'w') as f:      
      json.dump(data, f, indent=4) 


def get_training_session_data(training_session_id):
  """Retrieves an validates all the training session metadata given a training session id.
     Returns an object of type NerTrainingSession with the metadata."""
  res = NerTrainingSession(training_session_id=training_session_id, is_valid=False)
  directory_path = os.path.join("model_train_sessions",training_session_id)
  if not os.path.exists(directory_path):
    res.is_valid = False
    res.invalid_message = f"Session with path {directory_path} does not exits."
    return res 
    
  best_model_path = os.path.join(directory_path,"models","model-best")
  if not os.path.exists(best_model_path):
    res.is_valid = False
    res.invalid_message = f"Session with best model path does not exits. Path: {best_model_path}"
    return res 
  
  meta_data_file = os.path.join(best_model_path,"meta.json")
  if not os.path.exists(meta_data_file):
    res.is_valid = False
    res.invalid_message = f"Session with best model metadata file does not exists. File: {meta_data_file}."
    return res     
  try:
    with open(meta_data_file, 'r') as file:
        json_data = json.load(file)
        labels_node = json_data['labels']     
        if labels_node:
            ner_node = labels_node['ner']
            if ner_node:
              res.ner_fields = ner_node

        performance_node = json_data['performance']  
        if performance_node:
            res.performance = performance_node 

        res.date_created = json_data.get('date_created', '')  # Get date_created if it exists  
        res.training_description = json_data.get('training_description', '')  # Get training_description if it exists      
  except Exception as e:
    pass

  res.is_valid = True
  return res 



class NerTrainingSession:
   
   def __init__(self, training_session_id, is_valid=False):
      self.training_session_id = training_session_id
      self.is_valid = is_valid      
      self.invalid_message = ''
      self.ner_fields = []
      self.performance = None
      self.date_created = '' 
      self.training_description = ''   

@namespace_ner_train.route("/session/")
class SessionProfile(Resource):
   @namespace_ner_train.marshal_list_with(training_session_model)
   def get(self):
      """Get a list of training session metadata."""   
      directory_path = os.path.join("model_train_sessions")  
      if not os.path.exists(directory_path):
         return []
      
      folders = []
      for item in os.listdir(directory_path):
         item_path = os.path.join(directory_path, item)
         if os.path.isdir(item_path):
            folders.append(item)
  

      return [get_training_session_data(training_session_id) for training_session_id in folders]
            



@namespace_ner_train.route("/session/<training_session_id>")
@namespace_ner_train.param('training_session_id', 'Training session id obtained from the train process.')
@namespace_ner_train.response(401, 'Invalid session id.')
class SessionProfile(Resource):
   @namespace_ner_train.marshal_with(training_session_model)
   def get(self,training_session_id):
      """Get training session metadata given a training session id."""

      if not training_session_id:
       abort(401, f"Training Session ID is required.")  

      res = get_training_session_data(training_session_id)
      if not res.is_valid:
         abort(401, f"Session with id {training_session_id} is missing or invalid.") 
      
      return res
   
   def delete(self, training_session_id):
      """Remove a training session a training session id."""

      if not training_session_id:
         abort(401, f"Session id is required.") 

      dir_to_remove = os.path.join("model_train_sessions",training_session_id)       

      if not os.path.exists(dir_to_remove):
         abort(401, f"Session with id {training_session_id} is not found.") 

      success = try_to_delete_session_folder(dir_to_remove)
      return {'success':success}

      
   
   


def try_to_delete_session_folder(folder):
   '''Tries to remove a folder. No need to raise an error if unsuccess.'''
   success = False
   try:
        shutil.rmtree(folder)
        success = True
   except Exception as e:
      print(e)
      pass
   return success
   

   
    

def massage_data(data):
    '''Pre process string to remove new line characters, add comma punctuations etc.'''
    data = data.upper()
    cleansed_address1=re.sub(r'(,)(?!\s)',' ',data)
    cleansed_address2=re.sub(r'(\\n)',' ',cleansed_address1)
    cleansed_address3=re.sub(r'(?!\s)(-)(?!\s)',' - ',cleansed_address2)
    cleansed_address=re.sub(r'\.','',cleansed_address3)
    return cleansed_address
  
   

def create_entity_spans(data_frame,tag_list,text_to_parse_column, tag_suffix):  
  '''Create entity spans'''

  data_frame[text_to_parse_column] = data_frame[text_to_parse_column].apply(lambda x: massage_data(x))

  tag_suffix_len = len(tag_suffix)
  for tag in tag_list:
    original_col_name = tag[:-tag_suffix_len]
    data_frame[original_col_name] = data_frame[original_col_name].apply(lambda x: x.upper() if x else x)
    data_frame[tag]=data_frame.apply(lambda row:get_span(search_str=row[text_to_parse_column],
                                                        component=row[original_col_name],
                                                        label=original_col_name),
                                     axis=1)
  data_frame['EmptySpan']=data_frame.apply(lambda x: [], axis=1)

  for i in tag_list:
      data_frame['EntitySpans']=data_frame.apply(lambda row: extend_list(row['EmptySpan'],row[i]),axis=1)
      data_frame['EntitySpans']=data_frame[['EntitySpans',text_to_parse_column]].apply(lambda x: (x.iloc[1], x.iloc[0]),axis=1)
  return data_frame['EntitySpans']

def get_span(search_str = None, 
             component=None,
             label=None):
  '''Search for specified component and get the span.
  Eg: get_span(address="221 B, Baker Street, London",address_component="221",label="BUILDING_NO") would return (0,2,"BUILDING_NO")'''
  if not component or pd.isna(component) or str(component)=='NAN':
      pass
  else:
      
      #replace dot with empty space
      component1=re.sub(r'\.','',component)
      #normalize space between hyphens
      component2=re.sub(r'(?!\s)(-)(?!\s)',' - ',component1)      
      span=re.search('\\b(?:'+component2+')\\b',search_str)
      if (not span):
         abort(401, message=f'Error creating entity span. You may need to perform some data cleaning. Unable to find the component: "{component}" inside the string "{search_str}"')
      return (span.start(),span.end(),label)
  
def extend_list(entity_list,entity):
    if pd.isna(entity):
        return entity_list
    else:
        entity_list.append(entity)
        return entity_list
    
def get_doc_bin(data,nlp):
    '''Create DocBin object for building training/test corpus'''
    # the DocBin will store the example documents
    db = DocBin()
    for text, annotations in data:
        doc = nlp(text) #Construct a Doc object
        ents = []        

        for start, end, label in annotations:           
            span = doc.char_span(start, end, label=label)
            ents.append(span)

        filtered = filter_spans(ents)           
        
        doc.ents = filtered 
        db.add(doc)
    return db
    
 