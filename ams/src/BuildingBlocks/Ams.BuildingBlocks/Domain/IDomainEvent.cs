namespace Ams.BuildingBlocks.Domain;

/// <summary>
/// A fact that happened inside an aggregate. Events are immutable records;
/// integration events derived from them carry only IDs and minimal facts
/// (GDPR data-minimisation — never full PII).
/// </summary>
public interface IDomainEvent
{
    Guid EventId { get; }
    DateTimeOffset OccurredAt { get; }
}

// VERIFY: nothing framework-specific may leak into this interface — domain projects reference it.
