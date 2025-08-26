using CsvHelper.Configuration.Attributes;

namespace LoadAnalyzer;

/// <summary>
/// 'Agents Count', 'Batch Size', 'Sent', 'Confirmed', 'P95', 'Best Eps', 'Best Confirmed'
/// </summary>
public class CsvEntry
{
    [Name("Agents Count")]
    public int AgentsCount { get; set; }
    [Name("Batch Size")]
    public int BatchSize { get; set; }
    [Name("Sent")]
    public int BatchesSent { get; set; }
    [Name("Confirmed")]
    public int BatchesConfirmed { get; set; }
    [Name("P95")]
    public double P95 { get; set; }
    [Name("Best Eps")]
    public int BestEps { get; set; }
    [Name("Best Confirmed")]
    public int BestConfirmedEsp { get; set; }

    public override string ToString()
    {
        return $"Agents: {AgentsCount}, Batch: {BatchSize}, " +
            $"Sent: {BatchesSent}, Confirmed: {BatchesConfirmed}, " +
            $" P95: {P95}, Eps: {BestEps}, EpsConfirmed: {BestConfirmedEsp}";
    }
}
