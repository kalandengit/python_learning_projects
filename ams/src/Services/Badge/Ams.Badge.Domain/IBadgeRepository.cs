namespace Ams.Badge.Domain;

/// <summary>
/// Outbound port for the event-sourced Badge stream (Hexagonal architecture).
/// LoadAsync replays history; AppendAsync commits uncommitted events with
/// optimistic concurrency (unique (badge_id, version) in the store).
/// </summary>
public interface IBadgeRepository
{
    Task<BadgeAggregate?> LoadAsync(Guid badgeId, CancellationToken ct);

    /// <summary>
    /// Appends the aggregates' uncommitted events in ONE transaction, together
    /// with their outbox rows (ADR-019). Multiple aggregates in one call give
    /// the FR-023 atomic replace guarantee.
    /// Throws <see cref="ConcurrencyConflictException"/> on version conflicts.
    /// </summary>
    Task AppendAsync(IReadOnlyList<BadgeAggregate> aggregates, string actor, CancellationToken ct);
}

public sealed class ConcurrencyConflictException(Guid badgeId)
    : Exception($"Concurrent modification of badge {badgeId}; reload and retry.")
{
    public Guid BadgeId { get; } = badgeId;
}

/// <summary>Port for QR signing (adapter: Azure Key Vault, rotating keys).</summary>
public interface IQrSigner
{
    Task<string> CurrentKeyIdAsync(CancellationToken ct);
}

// VERIFY: interface stays in Domain (port); Npgsql/KeyVault types must never appear here.
