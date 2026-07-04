using System.Security.Cryptography;
using System.Text;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.Logging;
using StackExchange.Redis;

namespace Ams.BuildingBlocks.Web;

/// <summary>
/// Enforces the Idempotency-Key contract (ADR-017) on POST/PATCH:
///  - missing key            -> 400 problem+json
///  - first request          -> handler runs; response cached in Redis 24 h
///  - replay (same payload)  -> cached response + Idempotency-Replayed: true
///  - same key, new payload  -> 422 urn:ams:idempotency:payload-mismatch
/// Keys are scoped per authenticated principal.
/// </summary>
public sealed class IdempotencyKeyMiddleware(
    RequestDelegate next,
    IConnectionMultiplexer redis,
    ILogger<IdempotencyKeyMiddleware> logger)
{
    private static readonly TimeSpan Ttl = TimeSpan.FromHours(24);

    public async Task InvokeAsync(HttpContext context)
    {
        if (context.Request.Method is not ("POST" or "PATCH"))
        {
            await next(context);
            return;
        }

        if (!context.Request.Headers.TryGetValue("Idempotency-Key", out var keyHeader) ||
            !Guid.TryParse(keyHeader.ToString(), out var key))
        {
            await WriteProblem(context, StatusCodes.Status400BadRequest,
                "urn:ams:idempotency:missing-key",
                "Idempotency-Key header (UUID) is required on POST/PATCH.");
            return;
        }

        var principal = context.User.Identity?.Name ?? "anonymous";
        var requestHash = await HashRequestBodyAsync(context);
        var redisKey = $"idem:{principal}:{key:N}";
        var db = redis.GetDatabase();

        var cached = await db.HashGetAllAsync(redisKey);
        if (cached.Length > 0)
        {
            var stored = cached.ToDictionary(e => (string)e.Name!, e => (string)e.Value!);
            if (stored["hash"] != requestHash)
            {
                await WriteProblem(context, StatusCodes.Status422UnprocessableEntity,
                    "urn:ams:idempotency:payload-mismatch",
                    "This Idempotency-Key was already used with a different payload.");
                return;
            }

            logger.LogInformation("Idempotent replay for key {IdempotencyKey}", key);
            context.Response.StatusCode = int.Parse(stored["status"], System.Globalization.CultureInfo.InvariantCulture);
            context.Response.ContentType = "application/json";
            context.Response.Headers["Idempotency-Replayed"] = "true";
            await context.Response.WriteAsync(stored["body"]);
            return;
        }

        // Capture the downstream response so it can be cached.
        var originalBody = context.Response.Body;
        await using var buffer = new MemoryStream();
        context.Response.Body = buffer;
        try
        {
            await next(context);

            buffer.Position = 0;
            var bodyText = await new StreamReader(buffer, Encoding.UTF8).ReadToEndAsync();

            if (context.Response.StatusCode < 500)
            {
                await db.HashSetAsync(redisKey,
                [
                    new HashEntry("hash", requestHash),
                    new HashEntry("status", context.Response.StatusCode),
                    new HashEntry("body", bodyText),
                ]);
                await db.KeyExpireAsync(redisKey, Ttl);
            }

            buffer.Position = 0;
            await buffer.CopyToAsync(originalBody);
        }
        finally
        {
            context.Response.Body = originalBody;
        }
    }

    private static async Task<string> HashRequestBodyAsync(HttpContext context)
    {
        context.Request.EnableBuffering();
        using var sha = SHA256.Create();
        var hash = await sha.ComputeHashAsync(context.Request.Body);
        context.Request.Body.Position = 0;
        return Convert.ToHexString(hash);
    }

    private static Task WriteProblem(HttpContext context, int status, string type, string detail)
    {
        context.Response.StatusCode = status;
        context.Response.ContentType = "application/problem+json";
        var traceId = context.TraceIdentifier;
        return context.Response.WriteAsync(
            $$"""{"type":"{{type}}","title":"Idempotency error","status":{{status}},"detail":"{{detail}}","traceId":"{{traceId}}"}""");
    }
}

// VERIFY: Redis outage behavior — HashGetAllAsync will throw; wrap with a policy if the documented fallback (aggregate-level concurrency only) is enabled.
