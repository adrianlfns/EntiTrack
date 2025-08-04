using System.Security.Cryptography;

/// <summary>
/// Class in charge of encapsulating all API calls.
/// </summary>
class APIManager
{

    public class APIRes
    {

        /// <summary>
        /// Indicates if there was an exception during the call. See ErrorMessage for th error description
        /// </summary>
        public bool Success_IND { get; set; } = false;
        public string ErrorMessage { get; set; } = string.Empty;

        /// <summary>
        /// JSON resulting from the API call. 
        /// </summary>
        public string ResponseContent { get; set; } = string.Empty;

        /// <summary>
        /// Indicator to know if the API call returned a response between 200 and 299
        /// </summary>
        public bool IsSuccessStatusCode { get; set; }


    }

    StateContainer oStateContainer;

    public APIManager(StateContainer StateContainer)
    {
        oStateContainer = StateContainer;
    }



    /// <summary>
    /// Gets the list of Models given a google studio API key.
    /// </summary>
    /// <param name="strGoogleGenAIAPIKey"></param>
    /// <returns></returns>
    public async Task<APIRes> GenAI_GetGoogleStudioListOfModels(string strGoogleGenAIAPIKey)
    {
        APIRes res = new();
        try
        {
            using (HttpClient client = new())
            {
                using (HttpRequestMessage request = new())
                {
                    request.RequestUri = new Uri($"{oStateContainer.Base_EntiTrack_Endpoint}/gen_ai_ner/list_models_google_studio/{strGoogleGenAIAPIKey}");
                    request.Method = HttpMethod.Get;
                    request.Headers.Add("Accept", "*/*");

                    using (HttpResponseMessage response = await client.SendAsync(request))
                    {
                        response.EnsureSuccessStatusCode();
                        res.ResponseContent = await response.Content.ReadAsStringAsync();
                        oStateContainer.GoogleGenAIAPIKey = strGoogleGenAIAPIKey;
                        res.IsSuccessStatusCode = response.IsSuccessStatusCode;
                        res.Success_IND = true;
                    }
                }
            }
        }
        catch (Exception ex)
        {
            System.Console.WriteLine(ex.Message);
            res.ErrorMessage = $"Unable obtain the list of models. Possible cause: Invalid API key. Error Message: {ex.Message}";
        }
        return res;
    }

    /// <summary>
    /// Performs a single NER request using API
    /// </summary>
    /// <param name="strModelKey">Example models/gemini-2.0-flash</param>
    /// <param name="strTextToCheck"></param>
    /// <param name="oNerFields"></param>
    /// <returns></returns>
    public async Task<APIRes> GenAI_PerformGenAISingleNER(string strGoogleGenAIAPIKey, string strModelKey, string strTextToCheck, List<string> oNerFields)
    {
        APIRes res = new();
        try
        {

            //build the request payload (a json data) 
            PerformGenAINERRequestData oPerformGenAINERRequestData = new();
            oPerformGenAINERRequestData.text_to_check = strTextToCheck;
            oPerformGenAINERRequestData.model_key = strModelKey;
            oPerformGenAINERRequestData.ner_fields = oNerFields;
            string strRequestPayload = System.Text.Json.JsonSerializer.Serialize<PerformGenAINERRequestData>(oPerformGenAINERRequestData);



            using (HttpClient client = new())
            {
                using (HttpRequestMessage request = new())
                {



                    request.RequestUri = new Uri($"{oStateContainer.Base_EntiTrack_Endpoint}/gen_ai_ner/perform_ner/{strGoogleGenAIAPIKey}");
                    request.Method = HttpMethod.Post;
                    request.Headers.Add("Accept", "*/*");



                    var bodyString = strRequestPayload;
                    var content = new StringContent(bodyString, System.Text.Encoding.UTF8, "application/json");
                    request.Content = content;

                    using (HttpResponseMessage response = await client.SendAsync(request))
                    {
                        response.EnsureSuccessStatusCode();  //it i
                        res.ResponseContent = await response.Content.ReadAsStringAsync();
                        res.Success_IND = true;
                        res.IsSuccessStatusCode = response.IsSuccessStatusCode;
                        oStateContainer.GoogleGenAIAPIKey = strGoogleGenAIAPIKey;
                    }
                }
            }
        }
        catch (Exception ex)
        {
            System.Console.WriteLine(ex.Message);
            res.ErrorMessage = $"Unable to perform Gen AI NER. Possible cause: Invalid API key. Error Message: {ex.Message}";
        }
        return res;
    }


    /// <summary>
    /// Removes the training session given it's ID
    /// </summary>
    /// <param name="strTrainingSessionId"></param>
    /// <returns></returns>
    public async Task<APIRes> TrainedModel_RemoveSession(string strTrainingSessionId)
    {
        APIRes res = new();
        try
        {
            using (HttpClient client = new())
            {
                using (HttpRequestMessage request = new())
                {
                    request.RequestUri = new Uri($"{oStateContainer.Base_EntiTrack_Endpoint}/spacy_train_ner/session/{strTrainingSessionId} ");
                    request.Method = HttpMethod.Delete;
                    request.Headers.Add("Accept", "*/*");
                    using (HttpResponseMessage response = await client.SendAsync(request))
                    {
                        response.EnsureSuccessStatusCode();
                        res.ResponseContent = await response.Content.ReadAsStringAsync();
                        res.IsSuccessStatusCode = response.IsSuccessStatusCode;
                        res.Success_IND = true;
                    }
                }
            }

        }
        catch (Exception ex)
        {
            System.Console.WriteLine(ex.Message);
            res.ErrorMessage = "Unable to remove the training session." + ex.Message;
        }
        return res;
    }


    /// <summary>
    ///  List all the training sessions
    /// </summary>
    /// <returns></returns>
    public async Task<APIRes> TrainedModel_ListSessions()
    {
        APIRes res = new();
        try
        {
            using (HttpClient client = new())
            {
                using (HttpRequestMessage request = new())
                {
                    request.RequestUri = new Uri($"{oStateContainer.Base_EntiTrack_Endpoint}/spacy_train_ner/session/");
                    request.Method = HttpMethod.Get;
                    request.Headers.Add("Accept", "*/*");
                    using (HttpResponseMessage response = await client.SendAsync(request))
                    {
                        response.EnsureSuccessStatusCode();
                        res.ResponseContent = await response.Content.ReadAsStringAsync();
                        res.IsSuccessStatusCode = response.IsSuccessStatusCode;
                        res.Success_IND = true;
                    }
                }
            }
        }
        catch (Exception ex)
        {
            System.Console.WriteLine(ex.Message);
            res.ErrorMessage = "Unable to obtain training sessions. Possible cause: Invalid configuration. Error message: " + ex.Message;
        }
        return res;
    }


    /// <summary>
    /// Crates a new training session.
    /// </summary>
    /// <param name="oStream">CSV file stream</param>
    /// <param name="strFileName">Name of the uploaded file</param>
    /// <param name="strUnstructuredColumnName">Column name that represents the unstructured column.</param>
    /// <param name="strTrainingDescription">Brief description on what is the training for.</param>
    /// <returns></returns>
    public async Task<APIRes> TrainedModel_TrainNewModel(Stream oStream, string strFileName, string strUnstructuredColumnName, string strTrainingDescription)
    {
        APIRes res = new();
        try
        {
            string url = $"{oStateContainer.Base_EntiTrack_Endpoint}/spacy_train_ner/train";
            string fileContentType = "text/csv";

            using (HttpClient client = new())
            {
                client.Timeout = Timeout.InfiniteTimeSpan;
                using (MultipartFormDataContent form = new())
                {
                    StreamContent streamContent = new(oStream);
                    streamContent.Headers.ContentType = new System.Net.Http.Headers.MediaTypeHeaderValue(fileContentType);
                    form.Add(streamContent, "file", strFileName);
                    form.Add(new StringContent(strUnstructuredColumnName), "unstructured_column_name");
                    form.Add(new StringContent(strTrainingDescription), "training_description");

                    HttpResponseMessage response = await client.PostAsync(url, form);
                    res.IsSuccessStatusCode = response.IsSuccessStatusCode;
                    res.ResponseContent = await response.Content.ReadAsStringAsync();
                    res.Success_IND = true;
                }
            }
        }
        catch (Exception e)
        {
            Console.WriteLine($"An unexpected error occurred: {e.Message}");
            res.ErrorMessage = "Unable to obtain training sessions. Possible cause: Invalid configuration. Error message: " + e.Message;
        }
        return res;
    }


    /// <summary>
    /// Gets the metadata for given a training session ID
    /// </summary>
    /// <param name="strTrainingSessionId"></param>
    /// <returns></returns>
    public async Task<APIRes> TrainedModel_GetSessionMetadata(string strTrainingSessionId)
    {
        APIRes res = new();
        try
        {
            string url = $"{oStateContainer.Base_EntiTrack_Endpoint}/spacy_train_ner/session/{strTrainingSessionId}";

            using (HttpClient client = new())
            {
                using (HttpRequestMessage request = new())
                {
                    request.RequestUri = new Uri(url);
                    request.Method = HttpMethod.Get;
                    request.Headers.Add("Accept", "*/*");

                    using (HttpResponseMessage response = await client.SendAsync(request))
                    {
                        response.EnsureSuccessStatusCode();  //it i
                        res.ResponseContent = await response.Content.ReadAsStringAsync();
                        res.Success_IND = true;
                        res.IsSuccessStatusCode = response.IsSuccessStatusCode;
                    }
                }
            }
        }
        catch (Exception e)
        {
            Console.WriteLine($"An unexpected error occurred: {e.Message}");
            res.ErrorMessage = "Unable to obtain training session data. Error message: " + e.Message;
        }
        return res;
    }

    /// <summary>
    /// Performs a single NER given a training session and unstructured text
    /// </summary>
    /// <param name="strTrainingSessionId"></param>
    /// <param name="strUnstructuredText"></param>
    /// <returns></returns>
    public async Task<APIRes> TrainedModel_PerformSingleNER(string strTrainingSessionId, string strUnstructuredText)
    {
        APIRes res = new();
        try
        {
            using (HttpClient client = new())
            {
                client.DefaultRequestHeaders.Accept.Add(new System.Net.Http.Headers.MediaTypeWithQualityHeaderValue("application/json"));
                var formData = new Dictionary<string, string>
                {
                    { "text_to_check", strUnstructuredText },
                    { "training_session_id", strTrainingSessionId}
                };

                FormUrlEncodedContent content = new(formData);
                string url = $"{oStateContainer.Base_EntiTrack_Endpoint}/spacy_train_ner/perform_ner";


                using (HttpResponseMessage response = await client.PostAsync(url, content))
                {
                    response.EnsureSuccessStatusCode();
                    res.ResponseContent = await response.Content.ReadAsStringAsync();
                    res.Success_IND = true;
                    res.IsSuccessStatusCode = response.IsSuccessStatusCode;
                }
            }

        }
        catch (Exception e)
        {
            Console.WriteLine($"An unexpected error occurred: {e.Message}");
            res.ErrorMessage = "Unable to obtain training session data. Error message: " + e.Message;
        }
        return res;
    }
    

   
}