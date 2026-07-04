using MediatR;
using Ams.Badge.Domain;

namespace Ams.Badge.Application.IssueBadge;

/// <summary>Issue a badge for a cardholder (FR-019). CQRS write side.</summary>
public sealed record IssueBadgeCommand : IRequest<IssueBadgeResult>
{
    public required Guid CardholderId { get; init; }
    public required BadgeType BadgeType { get; init; }
    public required DateTimeOffset ValidFrom { get; init; }
    public required DateTimeOffset ValidUntil { get; init; }
    public Guid? SiteId { get; init; }
    /// <summary>Authenticated principal id — recorded as event actor, never a display name.</summary>
    public required string Actor { get; init; }
}

public sealed record IssueBadgeResult(
    Guid BadgeId,
    BadgeState State,
    DateTimeOffset ValidFrom,
    DateTimeOffset ValidUntil,
    long StreamVersion);

// VERIFY: result exposes StreamVersion so clients can do optimistic If-Match on follow-ups.
