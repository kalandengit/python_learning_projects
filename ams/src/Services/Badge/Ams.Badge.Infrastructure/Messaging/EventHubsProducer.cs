using System.Text;
using Azure.Identity;
using Azure.Messaging.EventHubs;
using Azure.Messaging.EventHubs.Producer;
using Microsoft.Extensions.Logging;
using Ams.BuildingBlocks.Messaging;

namespace Ams.Badge.Infrastructure.Messaging;

/// <summary>
/// Event Hubs adapter for IIntegrationEventPublisher. Partition key =
/// aggregate id (per-aggregate ordering, ADR-005); auth via managed identity
/// (Zero Trust: no connection strings, NFR-012).
/// </summary>
public sealed class EventHubsProducer : IIntegrationEventPublisher, IAsyncDisposable
{
    private readonly EventHubProducerClient _client;
    private readonly ILogger<EventHubsProducer> _logger;

    public EventHubsProducer(string fullyQualifiedNamespace, string hubName, ILogger<EventHubsProducer> logger)
    {
        _client = new EventHubProducerClient(
            fullyQualifiedNamespace, hubName, new DefaultAzureCredential());
        _logger = logger;
    }

    public async Task PublishAsync(IReadOnlyList<OutboxMessage> batch, CancellationToken ct)
    {
        // One send per partition key preserves per-aggregate ordering.
        foreach (var group in batch.GroupBy(m => m.AggregateId))
        {
            using var eventBatch = await _client.CreateBatchAsync(
                new CreateBatchOptions { PartitionKey = group.Key.ToString() }, ct);

            foreach (var message in group.OrderBy(m => m.OutboxId))
            {
                var eventData = new EventData(Encoding.UTF8.GetBytes(message.PayloadJson))
                {
                    ContentType = "application/json",
                    MessageId = message.OutboxId.ToString(),
                };
                eventData.Properties["eventType"] = message.EventType;
                eventData.Properties["schemaVersion"] = message.SchemaVersion;
                if (message.TraceParent is not null)
                    eventData.Properties["traceparent"] = message.TraceParent; // W3C context across the hub (Section 13.3)

                if (!eventBatch.TryAdd(eventData))
                    throw new InvalidOperationException(
                        $"Outbox message {message.OutboxId} exceeds the Event Hubs batch size.");
            }

            await _client.SendAsync(eventBatch, ct);
            _logger.LogDebug("Published {Count} events for aggregate {AggregateId}",
                group.Count(), group.Key);
        }
    }

    public ValueTask DisposeAsync() => _client.DisposeAsync();
}

// VERIFY: DefaultAzureCredential requires the pod's workload identity to hold "Azure Event Hubs Data Sender" on the namespace.
