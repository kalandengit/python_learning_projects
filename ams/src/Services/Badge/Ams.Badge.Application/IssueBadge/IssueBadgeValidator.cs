using FluentValidation;
using Ams.Badge.Domain;

namespace Ams.Badge.Application.IssueBadge;

public sealed class IssueBadgeValidator : AbstractValidator<IssueBadgeCommand>
{
    public IssueBadgeValidator()
    {
        RuleFor(x => x.CardholderId).NotEmpty();
        RuleFor(x => x.Actor).NotEmpty().MaximumLength(200);
        RuleFor(x => x.BadgeType).IsInEnum();

        RuleFor(x => x.ValidUntil)
            .GreaterThan(x => x.ValidFrom)
            .WithMessage("validUntil must be after validFrom.");

        RuleFor(x => x.ValidUntil)
            .GreaterThan(_ => DateTimeOffset.UtcNow)
            .WithMessage("Badge validity must end in the future.");

        // FR-025: temporary badges expire within 30 days.
        RuleFor(x => x)
            .Must(x => x.BadgeType != BadgeType.TemporaryRfid ||
                       x.ValidUntil - x.ValidFrom <= TimeSpan.FromDays(30))
            .WithMessage("Temporary badges must expire within 30 days (FR-025).")
            .WithName("validUntil");
    }
}

// VERIFY: domain re-checks FR-025 (defence-in-depth) — keep both in sync.
