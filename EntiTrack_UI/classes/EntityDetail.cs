using System.Text.Json.Serialization;

public class EntityDetail
{
    [JsonPropertyName("Entity Label:")]
    public string EntityLabel { get; set; } = string.Empty;

    [JsonPropertyName("Entity Text")]
    public string EntityText { get; set; } = string.Empty;

    [JsonPropertyName("Entity Start Index")] 
    public int EntityStartIndex { get; set; }

    [JsonPropertyName("Entity End Index")] 
    public int EntityEndIndex { get; set; }
}