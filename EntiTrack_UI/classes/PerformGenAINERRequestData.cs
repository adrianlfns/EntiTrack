public class PerformGenAINERRequestData
{
    public string model_key { get; set; } = string.Empty;
    public string text_to_check { get; set; } = string.Empty;
    public List<string>  ner_fields {get; set; } = [];
}