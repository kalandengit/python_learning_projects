namespace Ams.Badge.Domain;

public enum BadgeType
{
    Rfid,
    Qr,
    TemporaryRfid,
}

public enum BadgeState
{
    Requested,
    Issued,
    Active,
    Suspended,
    Revoked,
    Expired,
    Lost,
    Returned,
}

/// <summary>Validity window value object — always UTC, end after start.</summary>
public readonly record struct ValidityWindow
{
    public DateTimeOffset From { get; }
    public DateTimeOffset Until { get; }

    public ValidityWindow(DateTimeOffset from, DateTimeOffset until)
    {
        if (until <= from)
            throw new ArgumentException("Validity window end must be after start.", nameof(until));
        From = from.ToUniversalTime();
        Until = until.ToUniversalTime();
    }

    public bool Contains(DateTimeOffset instant) => instant >= From && instant < Until;

    /// <summary>FR-025: temporary badges may not exceed 30 days.</summary>
    public bool ExceedsTemporaryLimit => Until - From > TimeSpan.FromDays(30);
}

// VERIFY: record struct equality is value-based — intended for VO semantics.
