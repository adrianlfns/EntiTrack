
using System.Text.Json.Serialization;
public class EntsPerTypeDetail
{
    [JsonPropertyName("p")]
    public double Precision { get; set; }

    [JsonPropertyName("r")]
    public double Recall { get; set; }

    [JsonPropertyName("f")]
    public double F1Score { get; set; }
}