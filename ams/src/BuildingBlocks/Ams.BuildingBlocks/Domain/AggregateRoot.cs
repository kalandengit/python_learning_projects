namespace Ams.BuildingBlocks.Domain;

/// <summary>
/// Base for event-sourced aggregates (Hexagonal core, ADR-003).
/// State changes only via <see cref="Raise"/>, which routes through
/// <see cref="Apply"/> so replaying history and executing new commands
/// share one code path.
/// </summary>
public abstract class AggregateRoot<TId> where TId : notnull
{
    private readonly List<IDomainEvent> _uncommitted = [];

    public TId Id { get; protected set; } = default!;

    /// <summary>Version of the last committed event (optimistic concurrency token).</summary>
    public long Version { get; private set; }

    public IReadOnlyList<IDomainEvent> UncommittedEvents => _uncommitted;

    protected void Raise(IDomainEvent @event)
    {
        Apply(@event);
        _uncommitted.Add(@event);
    }

    /// <summary>Mutates state from an event. Must be side-effect free.</summary>
    protected abstract void Apply(IDomainEvent @event);

    /// <summary>Rehydrates the aggregate from its committed history.</summary>
    public void LoadFromHistory(IEnumerable<IDomainEvent> history)
    {
        foreach (var @event in history)
        {
            Apply(@event);
            Version++;
        }
    }

    public void MarkCommitted(long newVersion)
    {
        _uncommitted.Clear();
        Version = newVersion;
    }
}

// VERIFY: Version semantics must match the repository's expectedVersion handling (PostgresBadgeRepository).
