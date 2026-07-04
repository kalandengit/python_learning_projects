using Ams.BuildingBlocks.Domain;

namespace Ams.Badge.Domain;

/// <summary>
/// Strongly-typed domain events for the Badge stream (Section 2.2.3).
/// Records are immutable; payloads carry IDs and facts only — never PII.
/// Serialized names are stable contracts (ADR-014: additive-only evolution).
/// </summary>
public abstract record BadgeEvent : IDomainEvent
{
    public Guid EventId { get; init; } = Guid.CreateVersion7();
    public DateTimeOffset OccurredAt { get; init; } = DateTimeOffset.UtcNow;
    public required Guid BadgeId { get; init; }
}

public sealed record BadgeRequested : BadgeEvent
{
    public required Guid CardholderId { get; init; }
    public required BadgeType BadgeType { get; init; }
    public required DateTimeOffset ValidFrom { get; init; }
    public required DateTimeOffset ValidUntil { get; init; }
    public Guid? SiteId { get; init; }
}

public sealed record BadgeIssued : BadgeEvent
{
    public required Guid CardholderId { get; init; }
    public required BadgeType BadgeType { get; init; }
    public required DateTimeOffset ValidFrom { get; init; }
    public required DateTimeOffset ValidUntil { get; init; }
    /// <summary>Key Vault key id used to sign QR payloads; null for RFID.</summary>
    public string? QrKeyId { get; init; }
}

public sealed record BadgeActivated : BadgeEvent;

public sealed record BadgeSuspended : BadgeEvent
{
    public required string Reason { get; init; }
}

public sealed record BadgeReinstated : BadgeEvent;

public sealed record BadgeRevoked : BadgeEvent
{
    public required string Reason { get; init; }
}

public sealed record BadgeReportedLost : BadgeEvent;

public sealed record BadgeReplaced : BadgeEvent
{
    /// <summary>The replacement badge issued atomically with this revocation (FR-023).</summary>
    public required Guid NewBadgeId { get; init; }
    public required string Reason { get; init; }
}

public sealed record BadgeExpired : BadgeEvent;

public sealed record BadgeReturned : BadgeEvent;

// VERIFY: Guid.CreateVersion7() requires .NET 9+ — present on the pinned .NET 10 SDK.
