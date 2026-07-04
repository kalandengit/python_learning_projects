using System.Text.Json;
using System.Text.Json.Serialization;
using Npgsql;
using Ams.Badge.Domain;
using Ams.BuildingBlocks.Domain;

namespace Ams.Badge.Infrastructure.Persistence;

/// <summary>
/// PostgreSQL 18 adapter for the Badge event stream (port: IBadgeRepository).
/// - LoadAsync: replay badge_events ordered by version.
/// - AppendAsync: events + outbox rows in ONE transaction (ADR-019);
///   UNIQUE (badge_id, version) turns write races into ConcurrencyConflictException.
/// Multiple aggregates in one call = the FR-023 atomic-replace guarantee.
/// </summary>
public sealed class PostgresBadgeRepository(NpgsqlDataSource dataSource) : IBadgeRepository
{
    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        Converters = { new JsonStringEnumConverter() },
    };

    private static readonly Dictionary<string, Type> EventTypes =
        new[]
        {
            typeof(BadgeRequested), typeof(BadgeIssued), typeof(BadgeActivated),
            typeof(BadgeSuspended), typeof(BadgeReinstated), typeof(BadgeRevoked),
            typeof(BadgeReportedLost), typeof(BadgeReplaced), typeof(BadgeExpired),
            typeof(BadgeReturned),
        }.ToDictionary(t => t.Name, t => t);

    public async Task<BadgeAggregate?> LoadAsync(Guid badgeId, CancellationToken ct)
    {
        const string sql = """
            SELECT event_type, payload
            FROM badge.badge_events
            WHERE badge_id = @badgeId
            ORDER BY version
            """;

        await using var cmd = dataSource.CreateCommand(sql);
        cmd.Parameters.AddWithValue("badgeId", badgeId);

        var history = new List<IDomainEvent>();
        await using var reader = await cmd.ExecuteReaderAsync(ct);
        while (await reader.ReadAsync(ct))
        {
            var typeName = reader.GetString(0);
            var payload = reader.GetString(1);
            if (!EventTypes.TryGetValue(typeName, out var type))
                throw new InvalidOperationException($"Unknown badge event type '{typeName}' — missing upcaster (ADR-014)?");
            history.Add((IDomainEvent)JsonSerializer.Deserialize(payload, type, JsonOptions)!);
        }

        if (history.Count == 0) return null;

        var badge = (BadgeAggregate)Activator.CreateInstance(typeof(BadgeAggregate), nonPublic: true)!;
        badge.LoadFromHistory(history);
        return badge;
    }

    public async Task AppendAsync(
        IReadOnlyList<BadgeAggregate> aggregates, string actor, CancellationToken ct)
    {
        const string insertEvent = """
            INSERT INTO badge.badge_events (badge_id, version, event_type, payload, actor, occurred_at)
            VALUES (@badgeId, @version, @eventType, @payload::jsonb, @actor, @occurredAt)
            """;
        const string insertOutbox = """
            INSERT INTO messaging.outbox (aggregate_id, topic, event_type, payload)
            VALUES (@aggregateId, 'ams.badge', @eventType, @payload::jsonb)
            """;

        await using var connection = await dataSource.OpenConnectionAsync(ct);
        await using var tx = await connection.BeginTransactionAsync(ct);
        try
        {
            foreach (var aggregate in aggregates)
            {
                var version = aggregate.Version;
                foreach (var @event in aggregate.UncommittedEvents)
                {
                    version++;
                    var payload = JsonSerializer.Serialize(@event, @event.GetType(), JsonOptions);

                    await using (var cmd = new NpgsqlCommand(insertEvent, connection, tx))
                    {
                        cmd.Parameters.AddWithValue("badgeId", aggregate.Id);
                        cmd.Parameters.AddWithValue("version", version);
                        cmd.Parameters.AddWithValue("eventType", @event.GetType().Name);
                        cmd.Parameters.AddWithValue("payload", payload);
                        cmd.Parameters.AddWithValue("actor", actor);
                        cmd.Parameters.AddWithValue("occurredAt", @event.OccurredAt);
                        await cmd.ExecuteNonQueryAsync(ct);
                    }

                    await using (var cmd = new NpgsqlCommand(insertOutbox, connection, tx))
                    {
                        cmd.Parameters.AddWithValue("aggregateId", aggregate.Id);
                        cmd.Parameters.AddWithValue("eventType", ToTopicEventType(@event));
                        cmd.Parameters.AddWithValue("payload", payload);
                        await cmd.ExecuteNonQueryAsync(ct);
                    }
                }
            }

            await tx.CommitAsync(ct);

            foreach (var aggregate in aggregates)
                aggregate.MarkCommitted(aggregate.Version + aggregate.UncommittedEvents.Count);
        }
        catch (PostgresException ex) when (ex.SqlState == PostgresErrorCodes.UniqueViolation)
        {
            throw new ConcurrencyConflictException(aggregates[0].Id);
        }
    }

    private static string ToTopicEventType(IDomainEvent @event) => @event switch
    {
        BadgeRequested => "badge.requested",
        BadgeIssued => "badge.issued",
        BadgeActivated => "badge.activated",
        BadgeSuspended => "badge.suspended",
        BadgeReinstated => "badge.reinstated",
        BadgeRevoked => "badge.revoked",
        BadgeReportedLost => "badge.reported-lost",
        BadgeReplaced => "badge.replaced",
        BadgeExpired => "badge.expired",
        BadgeReturned => "badge.returned",
        _ => throw new InvalidOperationException($"Unmapped event {@event.GetType().Name}"),
    };
}

// VERIFY: Activator.CreateInstance(nonPublic: true) reaches the private rehydration ctor — swap for a static factory if trimming/AOT is enabled.
