namespace Ams.BuildingBlocks.Messaging;

/// <summary>
/// One row of the transactional outbox (ADR-019). Written in the same DB
/// transaction as the state change; drained by an OutboxDispatcher.
/// </summary>
public sealed record OutboxMessage
{
    public required Guid OutboxId { get; init; }
    public required Guid AggregateId { get; init; }
    public required string Topic { get; init; }
    public required string EventType { get; init; }
    public short SchemaVersion { get; init; } = 1;
    public required string PayloadJson { get; init; }
    public string? TraceParent { get; init; }
    public DateTimeOffset CreatedAt { get; init; } = DateTimeOffset.UtcNow;
}

/// <summary>Port: publish integration events (adapter: Event Hubs producer).</summary>
public interface IIntegrationEventPublisher
{
    Task PublishAsync(IReadOnlyList<OutboxMessage> batch, CancellationToken ct);
}

// VERIFY: PayloadJson is pre-serialized at write time so the dispatcher never needs domain types.
