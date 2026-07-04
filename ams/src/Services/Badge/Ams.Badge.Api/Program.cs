using System.Text.Json.Serialization;
using FluentValidation;
using MediatR;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using OpenTelemetry.Metrics;
using OpenTelemetry.Resources;
using OpenTelemetry.Trace;
using StackExchange.Redis;
using Ams.Badge.Api.Endpoints;
using Ams.Badge.Application.Behaviors;
using Ams.Badge.Application.IssueBadge;
using Ams.Badge.Domain;
using Ams.Badge.Infrastructure.Messaging;
using Ams.Badge.Infrastructure.Persistence;
using Ams.Badge.Infrastructure.Signing;
using Ams.BuildingBlocks.Messaging;
using Ams.BuildingBlocks.Web;

var builder = WebApplication.CreateBuilder(args);

// ---- Configuration (12-Factor: everything from env) -------------------------
var pgConnectionString = builder.Configuration.GetConnectionString("BadgeDb")
    ?? throw new InvalidOperationException("ConnectionStrings__BadgeDb is required.");
var redisConnection = builder.Configuration["Redis:Configuration"]
    ?? throw new InvalidOperationException("Redis__Configuration is required.");
var eventHubsNamespace = builder.Configuration["EventHubs:FullyQualifiedNamespace"]
    ?? throw new InvalidOperationException("EventHubs__FullyQualifiedNamespace is required.");
var keyVaultUri = builder.Configuration["KeyVault:Uri"]
    ?? throw new InvalidOperationException("KeyVault__Uri is required.");

// ---- AuthN/AuthZ (Zero Trust PEP-behind-PEP: APIM validates too) -------------
builder.Services
    .AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(options =>
    {
        options.Authority = builder.Configuration["Auth:Authority"]; // Entra ID tenant
        options.Audience = builder.Configuration["Auth:Audience"];
        options.TokenValidationParameters.ValidateIssuer = true;
    });
builder.Services.AddAuthorizationBuilder()
    .AddPolicy("badges:read", p => p.RequireAuthenticatedUser().RequireClaim("scp"))
    .AddPolicy("badges:write", p => p.RequireAuthenticatedUser().RequireClaim("scp"))
    .AddPolicy("badges:admin", p => p.RequireAuthenticatedUser().RequireRole("Badge.Admin"));

// ---- Persistence, cache, messaging ------------------------------------------
builder.Services.AddNpgsqlDataSource(pgConnectionString);
builder.Services.AddSingleton<IConnectionMultiplexer>(
    _ => ConnectionMultiplexer.Connect(redisConnection));
builder.Services.AddSingleton<IBadgeRepository, PostgresBadgeRepository>();
builder.Services.AddSingleton<IQrSigner>(sp => new KeyVaultQrSigner(
    new Uri(keyVaultUri),
    builder.Configuration["KeyVault:QrKeyName"] ?? "qr-badge-signing",
    sp.GetRequiredService<ILogger<KeyVaultQrSigner>>()));
builder.Services.AddSingleton<IIntegrationEventPublisher>(sp => new EventHubsProducer(
    eventHubsNamespace, "ams.badge", sp.GetRequiredService<ILogger<EventHubsProducer>>()));
builder.Services.AddHostedService<OutboxDispatcher>();

// ---- CQRS pipeline (ADR-002) --------------------------------------------------
builder.Services.AddMediatR(cfg =>
    cfg.RegisterServicesFromAssembly(typeof(IssueBadgeCommand).Assembly));
builder.Services.AddValidatorsFromAssembly(typeof(IssueBadgeValidator).Assembly);
builder.Services.AddTransient(typeof(IPipelineBehavior<,>), typeof(ValidationBehavior<,>));

// ---- RFC 7807 + JSON conventions ---------------------------------------------
builder.Services.AddProblemDetails(options =>
    options.CustomizeProblemDetails = ctx =>
        ctx.ProblemDetails.Extensions["traceId"] = ctx.HttpContext.TraceIdentifier);
builder.Services.ConfigureHttpJsonOptions(o =>
    o.SerializerOptions.Converters.Add(new JsonStringEnumConverter()));

// ---- Observability (NFR-018) ---------------------------------------------------
builder.Services.AddOpenTelemetry()
    .ConfigureResource(r => r.AddService("badge-service",
        serviceVersion: typeof(Program).Assembly.GetName().Version?.ToString()))
    .WithTracing(t => t
        .AddAspNetCoreInstrumentation()
        .AddHttpClientInstrumentation()
        .AddOtlpExporter())
    .WithMetrics(m => m
        .AddAspNetCoreInstrumentation()
        .AddRuntimeInstrumentation()
        .AddOtlpExporter());

builder.Services.AddHealthChecks()
    .AddNpgSql(pgConnectionString, name: "postgres", tags: ["ready"]);

var app = builder.Build();

app.UseExceptionHandler();  // problem+json for unhandled exceptions
app.UseStatusCodePages();
app.UseAuthentication();
app.UseAuthorization();
app.UseMiddleware<IdempotencyKeyMiddleware>(); // ADR-017

app.MapBadgeEndpoints();

app.MapHealthChecks("/healthz/live");
app.MapHealthChecks("/healthz/ready",
    new Microsoft.AspNetCore.Diagnostics.HealthChecks.HealthCheckOptions
    {
        Predicate = check => check.Tags.Contains("ready"),
    });

app.Run();

// VERIFY: OpenTelemetry.Instrumentation.Runtime package is pulled transitively? If AddRuntimeInstrumentation fails to resolve, add the OpenTelemetry.Instrumentation.Runtime package explicitly.
