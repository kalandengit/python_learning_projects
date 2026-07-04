using Ams.BuildingBlocks.Domain;

namespace Ams.Badge.Domain;

/// <summary>
/// Event-sourced aggregate root for the badge lifecycle state machine
/// (FR-020). Every mutation appends an event via Raise -> Apply; invalid
/// transitions throw <see cref="InvalidBadgeTransitionException"/> and no
/// event is appended.
/// </summary>
public sealed class BadgeAggregate : AggregateRoot<Guid>
{
    public Guid CardholderId { get; private set; }
    public BadgeType BadgeType { get; private set; }
    public BadgeState State { get; private set; }
    public ValidityWindow Validity { get; private set; }
    public string? QrKeyId { get; private set; }

    private BadgeAggregate() { } // rehydration

    // ---- Commands (behaviour) -----------------------------------------------

    public static BadgeAggregate Request(
        Guid badgeId, Guid cardholderId, BadgeType type, ValidityWindow validity, Guid? siteId)
    {
        if (type == BadgeType.TemporaryRfid && validity.ExceedsTemporaryLimit)
            throw new BadgeDomainException(
                "urn:ams:badge:temporary-window-exceeded",
                "Temporary badges must expire within 30 days (FR-025).");

        var badge = new BadgeAggregate();
        badge.Raise(new BadgeRequested
        {
            BadgeId = badgeId,
            CardholderId = cardholderId,
            BadgeType = type,
            ValidFrom = validity.From,
            ValidUntil = validity.Until,
            SiteId = siteId,
        });
        return badge;
    }

    public void Issue(string? qrKeyId)
    {
        EnsureTransition(BadgeState.Requested, nameof(Issue));
        if (BadgeType == BadgeType.Qr && string.IsNullOrEmpty(qrKeyId))
            throw new BadgeDomainException(
                "urn:ams:badge:qr-key-required",
                "QR badges must be issued with a signing key id (FR-024).");

        Raise(new BadgeIssued
        {
            BadgeId = Id,
            CardholderId = CardholderId,
            BadgeType = BadgeType,
            ValidFrom = Validity.From,
            ValidUntil = Validity.Until,
            QrKeyId = qrKeyId,
        });
    }

    public void Activate()
    {
        EnsureTransition(BadgeState.Issued, nameof(Activate));
        Raise(new BadgeActivated { BadgeId = Id });
    }

    public void Suspend(string reason)
    {
        EnsureTransition(BadgeState.Active, nameof(Suspend));
        Raise(new BadgeSuspended { BadgeId = Id, Reason = reason });
    }

    public void Reinstate()
    {
        EnsureTransition(BadgeState.Suspended, nameof(Reinstate));
        Raise(new BadgeReinstated { BadgeId = Id });
    }

    public void Revoke(string reason)
    {
        if (State is not (BadgeState.Issued or BadgeState.Active or BadgeState.Suspended or BadgeState.Lost))
            throw InvalidTransition(nameof(Revoke));
        Raise(new BadgeRevoked { BadgeId = Id, Reason = reason });
    }

    public void ReportLost()
    {
        EnsureTransition(BadgeState.Active, nameof(ReportLost));
        Raise(new BadgeReportedLost { BadgeId = Id });
        // FR-022: loss implies immediate revocation — appended atomically.
        Raise(new BadgeRevoked { BadgeId = Id, Reason = "REPORTED_LOST" });
    }

    /// <summary>
    /// FR-023: revoke this badge and mint the replacement in ONE uncommitted
    /// batch — the repository appends both aggregates' events transactionally,
    /// so no observable instant exists where both badges validate.
    /// </summary>
    public BadgeAggregate Replace(Guid newBadgeId, BadgeType newType, string reason, string? qrKeyId)
    {
        if (State is not (BadgeState.Active or BadgeState.Suspended or BadgeState.Lost))
            throw InvalidTransition(nameof(Replace));

        Raise(new BadgeReplaced { BadgeId = Id, NewBadgeId = newBadgeId, Reason = reason });
        Raise(new BadgeRevoked { BadgeId = Id, Reason = $"REPLACED:{reason}" });

        var replacement = Request(newBadgeId, CardholderId, newType, Validity, siteId: null);
        replacement.Issue(qrKeyId);
        return replacement;
    }

    public void Expire()
    {
        if (State is not (BadgeState.Issued or BadgeState.Active or BadgeState.Suspended))
            throw InvalidTransition(nameof(Expire));
        Raise(new BadgeExpired { BadgeId = Id });
    }

    public bool IsValidAt(DateTimeOffset instant) =>
        State == BadgeState.Active && Validity.Contains(instant);

    // ---- Apply (state mutation only; shared by replay and new commands) ------

    protected override void Apply(IDomainEvent @event)
    {
        switch (@event)
        {
            case BadgeRequested e:
                Id = e.BadgeId;
                CardholderId = e.CardholderId;
                BadgeType = e.BadgeType;
                Validity = new ValidityWindow(e.ValidFrom, e.ValidUntil);
                State = BadgeState.Requested;
                break;
            case BadgeIssued e:
                QrKeyId = e.QrKeyId;
                State = BadgeState.Issued;
                break;
            case BadgeActivated:
                State = BadgeState.Active;
                break;
            case BadgeSuspended:
                State = BadgeState.Suspended;
                break;
            case BadgeReinstated:
                State = BadgeState.Active;
                break;
            case BadgeReportedLost:
                State = BadgeState.Lost;
                break;
            case BadgeRevoked:
                State = BadgeState.Revoked;
                break;
            case BadgeReplaced:
                break; // revocation follows in the same batch
            case BadgeExpired:
                State = BadgeState.Expired;
                break;
            case BadgeReturned:
                State = BadgeState.Returned;
                break;
            default:
                throw new InvalidOperationException($"Unhandled event {@event.GetType().Name}");
        }
    }

    private void EnsureTransition(BadgeState required, string command)
    {
        if (State != required) throw InvalidTransition(command);
    }

    private InvalidBadgeTransitionException InvalidTransition(string command) =>
        new(Id, State, command);
}

public class BadgeDomainException(string errorType, string message) : Exception(message)
{
    public string ErrorType { get; } = errorType;
}

public sealed class InvalidBadgeTransitionException(Guid badgeId, BadgeState state, string command)
    : BadgeDomainException(
        "urn:ams:badge:invalid-transition",
        $"Cannot {command} badge {badgeId} in state {state}.")
{
    public BadgeState CurrentState { get; } = state;
}

// VERIFY: Apply must stay side-effect free — replay of a 10-year stream must not re-trigger behaviour.
