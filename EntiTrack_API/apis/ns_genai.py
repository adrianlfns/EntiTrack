from flask_restx import Resource,Namespace, fields, abort
from flask_cors import cross_origin
from google import genai
from typing import Any, Tuple
from pydantic import BaseModel, Field, create_model
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

namespace_ner_gen_ai = Namespace('GenAI NER (No training)', 
                             description='Perform NER without training a model.', 
                             path="/gen_ai_ner",
                              decorators=[cross_origin()])

##Request model for get gen AI list of models
model_profile = namespace_ner_gen_ai.model("ModelProfile",{
  'name': fields.String(required=True, description='Name of the model (model key)'),
  'display_name': fields.String(required=True, description='Display name'),
  'description': fields.String(required=True, description='Description'),
  'input_token_limit': fields.String(description='Input token limit'),
  'output_token_limit': fields.String(description='Output token limit'),
})

@namespace_ner_gen_ai.route("/list_models_google_studio/<google_studio_api_key>")
@namespace_ner_gen_ai.param('google_studio_api_key', 'Google studio API key. Go to https://aistudio.google.com/app/apikey to obtain your key.')
@namespace_ner_gen_ai.response(401, 'Invalid API key or unauthorized.')
class GenAIListModels(Resource):

  @namespace_ner_gen_ai.marshal_list_with(model_profile)
  def get(self, google_studio_api_key):
    """List the Gen AI Available models from google studio."""
    if not google_studio_api_key:
       abort(401, "API key is required.")

    genai_client = genai.Client(api_key=google_studio_api_key)
    try:
      return [mdl for mdl in genai_client.models.list().page]
    except Exception as e:
      abort(401,"Invalid API key")
      #TODO: put some internal error log here


##Request model for perform gen ai
gen_ai_ner_payload = namespace_ner_gen_ai.model("GenAIRequestPayload",{
  'model_key': fields.String(required=True, description='Model key'),
  'text_to_check': fields.String(required=True, description='Text analyze'),
  'ner_fields': fields.List(fields.String(required=True), description='Named Entities to be extracted')
})


FieldDetails = Tuple[type, str, list[Any]]  # field type, description, examples
def create_dynamic_model(model_name:str, fields_dict: dict[str, FieldDetails]) -> type[BaseModel]:
    """
    Create a dynamic Pydantic model based on the provided fields dictionary.
    
    :param fields_dict: A dictionary where keys are field names and values are tuples of (type, description)
    :return: A dynamically created Pydantic model
    """
    return create_model(

        model_name,
        **{
            field_name: (field_type, Field("", description=field_desc))
            for field_name, (field_type, field_desc) in fields_dict.items()
        }
    )


  
@namespace_ner_gen_ai.route("/perform_ner/<google_studio_api_key>")
@namespace_ner_gen_ai.param('google_studio_api_key', 'Google studio API key. Go to https://aistudio.google.com/app/apikey to obtain your key.')
@namespace_ner_gen_ai.expect(gen_ai_ner_payload)
@namespace_ner_gen_ai.response(401, 'Invalid API key or unauthorized.')
@namespace_ner_gen_ai.response(400, 'Invalid request.')
class GenAIPerformNER(Resource):
  def post(self, google_studio_api_key):
    """Perform NER with GenAI."""  

    #general validations
    if not google_studio_api_key:
       abort(401, message="Google AI studio key is required.") 

    model_key = namespace_ner_gen_ai.payload['model_key']
    if not model_key:
       abort(400, message="Model key key is required.") 

    text_to_check = namespace_ner_gen_ai.payload['text_to_check']
    if not text_to_check:
       abort(400, message="Text to check is required.") 

    ner_fields = namespace_ner_gen_ai.payload['ner_fields']
    if not ner_fields:
       abort(400, message="NER fields node is required.")
    
    if type(ner_fields) is not list:
      abort(400, message="NER fields node expected to be a list.")

    if len(ner_fields) == 0:
      abort(400, message="NER fields node expected to have at least one item.")



    #check if the the google studio api key is valid
    genai_client = genai.Client(api_key=google_studio_api_key)
    model_list = []
    try:
      model_list = [mdl.name for mdl in genai_client.models.list().page]
    except Exception as e:
      abort(401, message="Invalid model key or google ai service unavailable.") 
 
    #check that the model key is valid
    model_key = model_key.replace("models/","")
    if not any(map(lambda x: x.replace("models/","") == model_key, model_list)):
      abort(401, message=f"Model key {model_key} not found.") 

    #at this point the request is valid, 
    #build the dynamic pydantic object to be passed to the Gen AI chain 
    fields_tuples = [(field, (str,field )) for field in ner_fields]    
    fields_dict = dict(fields_tuples)
    dynamic_pydantic_request = create_dynamic_model("GenAITraiNERFormatInstr", fields_dict)    
    dynamic_pydantic_request.__doc__ = "NER information to extract"

    parser = JsonOutputParser(pydantic_object=dynamic_pydantic_request, return_exceptions=False)
    format_instructions = parser.get_format_instructions()

    #build the langchain template
    template = ChatPromptTemplate.from_messages([
      ("system", "You are an AI that generates JSON for Named Entity Recognition for a given text. If you dont know the answer to a field don't just set the field with empty string. Generate only the JSON according to the instructions provided to you."),
      ("human", (
          "Generate JSON about the user input according to the provided format instructions.\n" +
           "Format instructions {format_instructions}" + 
           "Input: {input}\n")
      )
    ])
   
    #prepare the chain     
    llm =  ChatGoogleGenerativeAI(model=model_key, google_api_key=google_studio_api_key)  

    chain = template.partial(format_instructions=format_instructions) | llm | parser

    chain_res = ""
    try:
      chain_res = chain.invoke(text_to_check)
    except Exception as e:
      abort(401, message="Unable to perform NER with the selected model. There are any reasons for this: Quota exceeded, Invalid model, Model not suitable for this task, Bad response from google API, etc.")
      
  
    return chain_res
