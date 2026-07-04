using MediatR;
using Microsoft.Extensions.Logging;
using Ams.Badge.Domain;

namespace Ams.Badge.Application.IssueBadge;

/// <summary>
/// Use case: request + issue a badge in one command (kiosk/operator flow).
/// The repository commits the events and the outbox rows in one transaction
/// (ADR-019); structured logging carries IDs only (PII rule, Section 13.2).
/// </summary>
public sealed class IssueBadgeHandler(
    IBadgeRepository repository,
    IQrSigner qrSigner,
    ILogger<IssueBadgeHandler> logger)
    : IRequestHandler<IssueBadgeCommand, IssueBadgeResult>
{
    public async Task<IssueBadgeResult> Handle(IssueBadgeCommand command, CancellationToken ct)
    {
        var badgeId = Guid.CreateVersion7();
        var validity = new ValidityWindow(command.ValidFrom, command.ValidUntil);

        var badge = BadgeAggregate.Request(
            badgeId, command.CardholderId, command.BadgeType, validity, command.SiteId);

        string? qrKeyId = null;
        if (command.BadgeType == BadgeType.Qr)
            qrKeyId = await qrSigner.CurrentKeyIdAsync(ct); // FR-024: signed QR, rotating keys

        badge.Issue(qrKeyId);

        await repository.AppendAsync([badge], command.Actor, ct);

        logger.LogInformation(
            "Badge issued {BadgeId} for cardholder {CardholderId} type {BadgeType} validUntil {ValidUntil}",
            badgeId, command.CardholderId, command.BadgeType, validity.Until);

        return new IssueBadgeResult(badgeId, badge.State, validity.From, validity.Until, badge.Version);
    }
}

// VERIFY: eligibility of the cardholder (Active status) is enforced via the cardholder_ref replica inside AppendAsync's transaction in the full implementation.
