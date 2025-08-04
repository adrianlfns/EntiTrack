using System.Text.Json.Serialization;
public class NerPerformance
{
    [JsonPropertyName("ents_f")]
    public double GlobalF1Score { get; set; }

    [JsonPropertyName("ents_p")]
    public double GlobalPrecision { get; set; }

    [JsonPropertyName("ents_r")]
    public double GlobalRecall { get; set; }

    [JsonPropertyName("ents_per_type")]
    public Dictionary<string, EntsPerTypeDetail> EntsPerType { get; set; }= default!;

    [JsonPropertyName("ner_loss")]
    public double NerLoss { get; set; }
}