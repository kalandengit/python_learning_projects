using System.Security.Claims;
using FluentValidation;
using MediatR;
using Microsoft.AspNetCore.Http.HttpResults;
using Microsoft.AspNetCore.Mvc;
using Ams.Badge.Application.IssueBadge;
using Ams.Badge.Application.RevokeBadge;
using Ams.Badge.Domain;

namespace Ams.Badge.Api.Endpoints;

/// <summary>
/// Minimal API inbound adapter: HTTP -> MediatR commands. Errors map to
/// RFC 7807 problem+json per the Section-9 status-code policy; the
/// Idempotency-Key contract is enforced by middleware (ADR-017).
/// </summary>
public static class BadgeEndpoints
{
    public static IEndpointRouteBuilder MapBadgeEndpoints(this IEndpointRouteBuilder app)
    {
        var group = app.MapGroup("/v1/badges").WithTags("Badges");

        group.MapPost("/", IssueAsync).RequireAuthorization("badges:write");
        group.MapPost("/{badgeId:guid}/revoke", RevokeAsync).RequireAuthorization("badges:admin");

        return app;
    }

    private static async Task<Results<Created<IssueBadgeResult>, ProblemHttpResult>> IssueAsync(
        [FromBody] IssueBadgeRequest request,
        ClaimsPrincipal user,
        IMediator mediator,
        HttpContext http,
        CancellationToken ct)
    {
        try
        {
            var result = await mediator.Send(new IssueBadgeCommand
            {
                CardholderId = request.CardholderId,
                BadgeType = request.BadgeType,
                ValidFrom = request.ValidFrom,
                ValidUntil = request.ValidUntil,
                SiteId = request.SiteId,
                Actor = ActorOf(user),
            }, ct);

            return TypedResults.Created($"/v1/badges/{result.BadgeId}", result);
        }
        catch (ValidationException ex)
        {
            return ValidationProblem(http, ex);
        }
        catch (BadgeDomainException ex)
        {
            return DomainProblem(http, ex, StatusCodes.Status422UnprocessableEntity);
        }
    }

    private static async Task<Results<Ok<RevokeBadgeResult>, ProblemHttpResult>> RevokeAsync(
        Guid badgeId,
        [FromBody] RevokeBadgeRequest request,
        ClaimsPrincipal user,
        IMediator mediator,
        HttpContext http,
        CancellationToken ct)
    {
        try
        {
            var result = await mediator.Send(new RevokeBadgeCommand
            {
                BadgeId = badgeId,
                Reason = request.Reason,
                Comment = request.Comment,
                Actor = ActorOf(user),
            }, ct);

            return TypedResults.Ok(result);
        }
        catch (ValidationException ex)
        {
            return ValidationProblem(http, ex);
        }
        catch (BadgeNotFoundException)
        {
            return TypedResults.Problem(
                type: "urn:ams:badge:not-found",
                title: "Badge not found",
                statusCode: StatusCodes.Status404NotFound,
                instance: http.Request.Path,
                extensions: TraceExtensions(http));
        }
        catch (InvalidBadgeTransitionException ex)
        {
            return DomainProblem(http, ex, StatusCodes.Status409Conflict);
        }
        catch (ConcurrencyConflictException)
        {
            return TypedResults.Problem(
                type: "urn:ams:badge:concurrency-conflict",
                title: "Concurrent modification",
                detail: "The badge was modified by another request; retry.",
                statusCode: StatusCodes.Status409Conflict,
                instance: http.Request.Path,
                extensions: TraceExtensions(http));
        }
    }

    private static string ActorOf(ClaimsPrincipal user) =>
        user.FindFirstValue(ClaimTypes.NameIdentifier)
        ?? user.FindFirstValue("oid")
        ?? "unknown";

    private static ProblemHttpResult ValidationProblem(HttpContext http, ValidationException ex) =>
        TypedResults.Problem(
            type: "urn:ams:validation:failed",
            title: "Validation failed",
            detail: string.Join(" ", ex.Errors.Select(e => e.ErrorMessage)),
            statusCode: StatusCodes.Status422UnprocessableEntity,
            instance: http.Request.Path,
            extensions: TraceExtensions(http));

    private static ProblemHttpResult DomainProblem(HttpContext http, BadgeDomainException ex, int status) =>
        TypedResults.Problem(
            type: ex.ErrorType,
            title: "Badge rule violation",
            detail: ex.Message,
            statusCode: status,
            instance: http.Request.Path,
            extensions: TraceExtensions(http));

    private static Dictionary<string, object?> TraceExtensions(HttpContext http) =>
        new() { ["traceId"] = http.TraceIdentifier };
}

public sealed record IssueBadgeRequest(
    Guid CardholderId,
    BadgeType BadgeType,
    DateTimeOffset ValidFrom,
    DateTimeOffset ValidUntil,
    Guid? SiteId);

public sealed record RevokeBadgeRequest(string Reason, string? Comment);

// VERIFY: TypedResults.Problem 'extensions' parameter shape — confirm against the pinned ASP.NET Core 10 API surface.
