using Ams.Badge.Domain;
using Xunit;

namespace Ams.Badge.Tests;

public class BadgeAggregateTests
{
    private static readonly ValidityWindow Week =
        new(DateTimeOffset.UtcNow, DateTimeOffset.UtcNow.AddDays(7));

    private static BadgeAggregate ActiveBadge()
    {
        var badge = BadgeAggregate.Request(
            Guid.CreateVersion7(), Guid.CreateVersion7(), BadgeType.Rfid, Week, null);
        badge.Issue(qrKeyId: null);
        badge.Activate();
        return badge;
    }

    [Fact]
    public void Lifecycle_happy_path_reaches_active()
    {
        var badge = ActiveBadge();
        Assert.Equal(BadgeState.Active, badge.State);
        // Requested + Issued + Activated
        Assert.Equal(3, badge.UncommittedEvents.Count);
    }

    [Fact]
    public void Revoked_badge_cannot_be_activated_and_no_event_is_appended()
    {
        var badge = ActiveBadge();
        badge.Revoke("SECURITY");
        var eventsBefore = badge.UncommittedEvents.Count;

        var ex = Assert.Throws<InvalidBadgeTransitionException>(badge.Activate);

        Assert.Equal("urn:ams:badge:invalid-transition", ex.ErrorType); // FR-020
        Assert.Equal(eventsBefore, badge.UncommittedEvents.Count);
    }

    [Fact]
    public void ReportLost_immediately_revokes()
    {
        var badge = ActiveBadge();
        badge.ReportLost();
        Assert.Equal(BadgeState.Revoked, badge.State); // FR-022
    }

    [Fact]
    public void Replace_revokes_old_and_issues_new_in_one_batch()
    {
        var badge = ActiveBadge();
        var replacement = badge.Replace(Guid.CreateVersion7(), BadgeType.Rfid, "DAMAGED", null);

        Assert.Equal(BadgeState.Revoked, badge.State);            // FR-023
        Assert.Equal(BadgeState.Issued, replacement.State);
        Assert.Contains(badge.UncommittedEvents, e => e is BadgeReplaced);
        Assert.Contains(badge.UncommittedEvents, e => e is BadgeRevoked);
    }

    [Fact]
    public void Temporary_badge_over_30_days_is_rejected()
    {
        var tooLong = new ValidityWindow(DateTimeOffset.UtcNow, DateTimeOffset.UtcNow.AddDays(45));

        var ex = Assert.Throws<BadgeDomainException>(() =>
            BadgeAggregate.Request(
                Guid.CreateVersion7(), Guid.CreateVersion7(), BadgeType.TemporaryRfid, tooLong, null));

        Assert.Equal("urn:ams:badge:temporary-window-exceeded", ex.ErrorType); // FR-025
    }

    [Fact]
    public void Qr_badge_requires_signing_key()
    {
        var badge = BadgeAggregate.Request(
            Guid.CreateVersion7(), Guid.CreateVersion7(), BadgeType.Qr, Week, null);

        var ex = Assert.Throws<BadgeDomainException>(() => badge.Issue(qrKeyId: null));
        Assert.Equal("urn:ams:badge:qr-key-required", ex.ErrorType); // FR-024
    }

    [Fact]
    public void Replay_from_history_reconstructs_state()
    {
        var source = ActiveBadge();
        var history = source.UncommittedEvents.ToList();

        var rehydrated = (BadgeAggregate)Activator.CreateInstance(
            typeof(BadgeAggregate), nonPublic: true)!;
        rehydrated.LoadFromHistory(history);

        Assert.Equal(source.Id, rehydrated.Id);
        Assert.Equal(BadgeState.Active, rehydrated.State);
        Assert.Equal(3, rehydrated.Version);
        Assert.Empty(rehydrated.UncommittedEvents);
    }

    [Fact]
    public void IsValidAt_respects_state_and_window()
    {
        var badge = ActiveBadge();
        Assert.True(badge.IsValidAt(DateTimeOffset.UtcNow.AddDays(1)));
        Assert.False(badge.IsValidAt(DateTimeOffset.UtcNow.AddDays(30)));

        badge.Revoke("ADMIN");
        Assert.False(badge.IsValidAt(DateTimeOffset.UtcNow.AddDays(1)));
    }
}

// VERIFY: tests run with `dotnet test src/Ams.sln` — no external dependencies required.
