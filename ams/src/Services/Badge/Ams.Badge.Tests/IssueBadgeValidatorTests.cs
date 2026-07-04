using Ams.Badge.Application.IssueBadge;
using Ams.Badge.Domain;
using Xunit;

namespace Ams.Badge.Tests;

public class IssueBadgeValidatorTests
{
    private readonly IssueBadgeValidator _validator = new();

    private static IssueBadgeCommand Valid() => new()
    {
        CardholderId = Guid.CreateVersion7(),
        BadgeType = BadgeType.Rfid,
        ValidFrom = DateTimeOffset.UtcNow,
        ValidUntil = DateTimeOffset.UtcNow.AddDays(365),
        Actor = "0197a1b2-oid",
    };

    [Fact]
    public void Valid_command_passes()
    {
        Assert.True(_validator.Validate(Valid()).IsValid);
    }

    [Fact]
    public void Window_end_before_start_fails()
    {
        var cmd = Valid() with
        {
            ValidFrom = DateTimeOffset.UtcNow.AddDays(2),
            ValidUntil = DateTimeOffset.UtcNow.AddDays(1),
        };
        var result = _validator.Validate(cmd);
        Assert.False(result.IsValid);
    }

    [Fact]
    public void Temporary_badge_over_30_days_fails()
    {
        var cmd = Valid() with
        {
            BadgeType = BadgeType.TemporaryRfid,
            ValidUntil = DateTimeOffset.UtcNow.AddDays(60),
        };
        var result = _validator.Validate(cmd);
        Assert.False(result.IsValid);
        Assert.Contains(result.Errors, e => e.ErrorMessage.Contains("FR-025"));
    }

    [Fact]
    public void Empty_cardholder_fails()
    {
        var cmd = Valid() with { CardholderId = Guid.Empty };
        Assert.False(_validator.Validate(cmd).IsValid);
    }
}

// VERIFY: `with` on the command record requires init-only properties — matches IssueBadgeCommand.
