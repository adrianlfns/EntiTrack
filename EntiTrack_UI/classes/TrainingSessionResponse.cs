using System.Text.Json.Serialization;

public class TrainingSessionResponse
{
    [JsonPropertyName("training_session_id")]
    public Guid TrainingSessionId { get; set; }

    [JsonPropertyName("is_valid")]
    public bool IsValid { get; set; }

    [JsonPropertyName("invalid_message")]
    public string InvalidMessage { get; set; } = string.Empty;

    [JsonPropertyName("ner_fields")]
    public List<string> NerFields { get; set; } = new List<string>();

    [JsonPropertyName("performance")]
    public NerPerformance Performance { get; set; } = default!;

    [JsonPropertyName("date_created")]
    public string DateCreated { get; set; } = string.Empty;

    [JsonPropertyName("training_description")]
    public string TrainingDescription { get; set; } = string.Empty;
}