


using Microsoft.AspNetCore.Components.WebAssembly.Hosting;

public class StateContainer
{
    IConfiguration oConfiguration;
    Microsoft.AspNetCore.Components.WebAssembly.Hosting.IWebAssemblyHostEnvironment oHostEnvironment;

    public StateContainer(IConfiguration Configuration, Microsoft.AspNetCore.Components.WebAssembly.Hosting.IWebAssemblyHostEnvironment HostEnvironment)
    {
        oConfiguration = Configuration;
        oHostEnvironment = HostEnvironment;
    }

    public string Base_EntiTrack_Endpoint
    {
        get
        {
            if (oHostEnvironment.IsDevelopment())
            {              
                return Convert.ToString(oConfiguration["base_entitrack_endpoint"])!;
            } 
            else
            {
                Uri oURI = new Uri(oHostEnvironment.BaseAddress);
                string baseUrl = $"{oURI.Scheme}://{oURI.Host}:{oURI.Port}/";
                return baseUrl;
            }           
        }
     }

    private string? mstrGoogleGenAIAPIKey;

    public string GoogleGenAIAPIKey
    {
        get => mstrGoogleGenAIAPIKey ?? string.Empty;
        set
        {
            mstrGoogleGenAIAPIKey = value;
            NotifyStateChanged();
        }
    }

    private string? mstrSelectedGenAIModelKey;
    public string SelectedGenAIModelKey
    {
        get => mstrSelectedGenAIModelKey ?? string.Empty;
        set
        {
            mstrSelectedGenAIModelKey = value;
            NotifyStateChanged();
        }
    }

    private IEnumerable<ModelData> oModelDataCol = Enumerable.Empty<ModelData>().ToList();

    public IEnumerable<ModelData> ModelDataCol
    {
        get
        {            
            return oModelDataCol;
        } 
        set
        {
            oModelDataCol = value;
            NotifyStateChanged();
        }
    }

    public event Action? OnChange;

    private void NotifyStateChanged() => OnChange?.Invoke();
}