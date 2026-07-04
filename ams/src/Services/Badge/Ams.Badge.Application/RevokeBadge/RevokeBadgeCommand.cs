using FluentValidation;
using MediatR;
using Microsoft.Extensions.Logging;
using Ams.Badge.Domain;

namespace Ams.Badge.Application.RevokeBadge;

/// <summary>Revoke a badge (FR-021/FR-022). Propagation SLO: edges <= 5 s P99.</summary>
public sealed record RevokeBadgeCommand : IRequest<RevokeBadgeResult>
{
    public required Guid BadgeId { get; init; }
    public required string Reason { get; init; }
    public string? Comment { get; init; }
    public required string Actor { get; init; }
}

public sealed record RevokeBadgeResult(Guid BadgeId, BadgeState State, long StreamVersion);

public sealed class RevokeBadgeValidator : AbstractValidator<RevokeBadgeCommand>
{
    private static readonly string[] AllowedReasons =
        ["REPORTED_LOST", "OFFBOARDED", "SECURITY", "CONTRACT_ENDED", "DAMAGED", "ADMIN"];

    public RevokeBadgeValidator()
    {
        RuleFor(x => x.BadgeId).NotEmpty();
        RuleFor(x => x.Actor).NotEmpty();
        RuleFor(x => x.Reason)
            .NotEmpty()
            .Must(r => AllowedReasons.Contains(r))
            .WithMessage($"Reason must be one of: {string.Join(", ", AllowedReasons)}.");
        RuleFor(x => x.Comment).MaximumLength(1000);
    }
}

public sealed class RevokeBadgeHandler(
    IBadgeRepository repository,
    ILogger<RevokeBadgeHandler> logger)
    : IRequestHandler<RevokeBadgeCommand, RevokeBadgeResult>
{
    public async Task<RevokeBadgeResult> Handle(RevokeBadgeCommand command, CancellationToken ct)
    {
        var badge = await repository.LoadAsync(command.BadgeId, ct)
            ?? throw new BadgeNotFoundException(command.BadgeId);

        badge.Revoke(command.Reason);
        await repository.AppendAsync([badge], command.Actor, ct);

        logger.LogWarning(
            "Badge revoked {BadgeId} reason {Reason} by {Actor}",
            command.BadgeId, command.Reason, command.Actor);

        return new RevokeBadgeResult(badge.Id, badge.State, badge.Version);
    }
}

public sealed class BadgeNotFoundException(Guid badgeId)
    : Exception($"Badge {badgeId} does not exist.")
{
    public Guid BadgeId { get; } = badgeId;
}

// VERIFY: the outbox row written by AppendAsync drives the <=5 s propagation SLO — dispatcher interval is 200 ms (OutboxDispatcher).
