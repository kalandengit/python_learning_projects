using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using Npgsql;
using Ams.BuildingBlocks.Messaging;

namespace Ams.Badge.Infrastructure.Messaging;

/// <summary>
/// Background service draining the transactional outbox to Event Hubs
/// (ADR-019). FOR UPDATE SKIP LOCKED lets replicas run dispatchers
/// concurrently without double-claiming; delivery is at-least-once and
/// consumers dedupe via the inbox table. 200 ms poll keeps revocation
/// propagation inside its 5 s P99 budget (NFR-013).
/// </summary>
public sealed class OutboxDispatcher(
    NpgsqlDataSource dataSource,
    IIntegrationEventPublisher publisher,
    ILogger<OutboxDispatcher> logger) : BackgroundService
{
    private const int BatchSize = 100;
    private static readonly TimeSpan PollInterval = TimeSpan.FromMilliseconds(200);
    private static readonly TimeSpan ErrorBackoff = TimeSpan.FromSeconds(5);

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        logger.LogInformation("Outbox dispatcher started (batch {BatchSize}, poll {Poll} ms)",
            BatchSize, PollInterval.TotalMilliseconds);

        while (!stoppingToken.IsCancellationRequested)
        {
            try
            {
                var drained = await DrainOnceAsync(stoppingToken);
                if (drained < BatchSize)
                    await Task.Delay(PollInterval, stoppingToken);
            }
            catch (OperationCanceledException) when (stoppingToken.IsCancellationRequested)
            {
                break;
            }
            catch (Exception ex)
            {
                logger.LogError(ex, "Outbox drain failed; backing off {Backoff}s", ErrorBackoff.TotalSeconds);
                await Task.Delay(ErrorBackoff, stoppingToken);
            }
        }
    }

    private async Task<int> DrainOnceAsync(CancellationToken ct)
    {
        const string claimSql = """
            SELECT outbox_id, aggregate_id, topic, event_type, schema_version, payload::text, trace_parent
            FROM messaging.outbox
            WHERE processed_at IS NULL
            ORDER BY outbox_id
            LIMIT @batch
            FOR UPDATE SKIP LOCKED
            """;
        const string markSql = """
            UPDATE messaging.outbox
            SET processed_at = now(), attempts = attempts + 1
            WHERE outbox_id = ANY(@ids)
            """;

        await using var connection = await dataSource.OpenConnectionAsync(ct);
        await using var tx = await connection.BeginTransactionAsync(ct);

        var messages = new List<OutboxMessage>(BatchSize);
        await using (var cmd = new NpgsqlCommand(claimSql, connection, tx))
        {
            cmd.Parameters.AddWithValue("batch", BatchSize);
            await using var reader = await cmd.ExecuteReaderAsync(ct);
            while (await reader.ReadAsync(ct))
            {
                messages.Add(new OutboxMessage
                {
                    OutboxId = reader.GetGuid(0),
                    AggregateId = reader.GetGuid(1),
                    Topic = reader.GetString(2),
                    EventType = reader.GetString(3),
                    SchemaVersion = reader.GetInt16(4),
                    PayloadJson = reader.GetString(5),
                    TraceParent = reader.IsDBNull(6) ? null : reader.GetString(6),
                });
            }
        }

        if (messages.Count == 0)
        {
            await tx.RollbackAsync(ct);
            return 0;
        }

        // Publish BEFORE marking processed: a crash between the two replays the
        // batch (at-least-once) — never loses it.
        await publisher.PublishAsync(messages, ct);

        await using (var cmd = new NpgsqlCommand(markSql, connection, tx))
        {
            cmd.Parameters.AddWithValue("ids", messages.Select(m => m.OutboxId).ToArray());
            await cmd.ExecuteNonQueryAsync(ct);
        }

        await tx.CommitAsync(ct);
        logger.LogDebug("Dispatched {Count} outbox messages", messages.Count);
        return messages.Count;
    }
}

// VERIFY: rows stay locked while publishing — keep BatchSize×publish-latency well under any statement/transaction timeout.
