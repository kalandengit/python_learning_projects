using Azure.Identity;
using Azure.Security.KeyVault.Keys;
using Microsoft.Extensions.Logging;
using Ams.Badge.Domain;

namespace Ams.Badge.Infrastructure.Signing;

/// <summary>
/// Key Vault adapter for the IQrSigner port (FR-024). The badge stream stores
/// only the key *id*; signing/verification use the HSM-held key. Rotation:
/// a new key version simply becomes "current" — old QR codes verify against
/// their recorded key id until they expire.
/// </summary>
public sealed class KeyVaultQrSigner : IQrSigner
{
    private readonly KeyClient _keyClient;
    private readonly string _keyName;
    private readonly ILogger<KeyVaultQrSigner> _logger;

    // Key id cached briefly; rotation must be visible within a minute.
    private string? _cachedKeyId;
    private DateTimeOffset _cacheUntil = DateTimeOffset.MinValue;
    private readonly SemaphoreSlim _refreshLock = new(1, 1);

    public KeyVaultQrSigner(Uri vaultUri, string keyName, ILogger<KeyVaultQrSigner> logger)
    {
        _keyClient = new KeyClient(vaultUri, new DefaultAzureCredential());
        _keyName = keyName;
        _logger = logger;
    }

    public async Task<string> CurrentKeyIdAsync(CancellationToken ct)
    {
        if (_cachedKeyId is not null && DateTimeOffset.UtcNow < _cacheUntil)
            return _cachedKeyId;

        await _refreshLock.WaitAsync(ct);
        try
        {
            if (_cachedKeyId is null || DateTimeOffset.UtcNow >= _cacheUntil)
            {
                var key = await _keyClient.GetKeyAsync(_keyName, cancellationToken: ct);
                _cachedKeyId = key.Value.Id.ToString();
                _cacheUntil = DateTimeOffset.UtcNow.AddMinutes(1);
                _logger.LogInformation("QR signing key refreshed: {KeyId}", _cachedKeyId);
            }
            return _cachedKeyId;
        }
        finally
        {
            _refreshLock.Release();
        }
    }
}

// VERIFY: requires Azure.Security.KeyVault.Keys package + "Key Vault Crypto User" role for the workload identity.
