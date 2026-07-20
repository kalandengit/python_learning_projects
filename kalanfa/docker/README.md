# Kalanfa Official Container Image

The official container image for Kalanfa, an offline learning platform designed for low-resource communities.

> [!NOTE]
> All examples use `docker` but should also work with `podman`

## Quick Start

```bash
docker run -d \
  -v /path/to/data:/kalanfa \
  -p 8080:8080 \
  -p 8081:8081 \
  ghcr.io/learningequality/kalanfa:latest
```

Then access Kalanfa at `http://localhost:8080`.

## Required Volume Mount

**You must mount storage to `/kalanfa`**. This can be any mount type (bind mount, named volume, etc.), and is where Kalanfa stores all its data including:

- Database files
- Content cache
- Configuration files
- User data
- Node ID for Morango sync

Without a mounted `/kalanfa` path, the container will refuse to start. Use a consistent mount so Kalanfa data persists predictably across container updates and restarts.

### Why This Is Required

Kalanfa requires persistent storage for:

1. **Database** - SQLite database with facility, user, and lesson data
2. **Content** - Downloaded educational content from channels
3. **Node ID** - Unique identifier for Morango synchronization (auto-generated on first run)

## Ports

The image exposes two ports:

| Port | Purpose |
|------|---------|
| 8080 | Main Kalanfa web server |
| 8081 | Zip content server (for serving content from .zip archives) |

Both ports should be exposed when running the container. The zip content port is required for Kalanfa to serve content from compressed archive files (H5P, Perseus, etc.).

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `KALANFA_HOME` | `/kalanfa` | Directory for Kalanfa data (must be mounted) |
| `KALANFA_HTTP_PORT` | `8080` | Port for the main web server |
| `KALANFA_ZIP_CONTENT_PORT` | `8081` | Port for zip content server |
| `MORANGO_SYSTEM_ID` | (auto-generated) | Morango system ID (auto-set from stored node ID) |
| `MORANGO_NODE_ID` | (auto-generated) | Morango node ID (auto-set from stored node ID) |

## Example Commands

### Basic Run

```bash
docker run -d \
  -v /srv/kalanfa:/kalanfa \
  -p 8080:8080 \
  -p 8081:8081 \
  --name kalanfa \
  ghcr.io/learningequality/kalanfa:latest
```

### With Specific Version

```bash
docker run -d \
  -v /srv/kalanfa:/kalanfa \
  -p 8080:8080 \
  -p 8081:8081 \
  ghcr.io/learningequality/kalanfa:0.19.0
```

### Compose

`compose.yml`:

```yaml
services:
  kalanfa:
    image: ghcr.io/learningequality/kalanfa:latest
    ports:
      - "8080:8080"
      - "8081:8081"
    volumes:
      - ./kalanfa-data:/kalanfa
    restart: unless-stopped
```

```bash
docker compose up -d
```

### View Logs

```bash
docker logs -f kalanfa
```

### Execute Commands in Running Container

```bash
docker exec -it kalanfa kalanfa manage --help
```

## Image Tags

- `latest` - Latest stable release
- `0.19` - Latest patch release for version 0.19.x
- `0.19.0` - Specific version

## Architecture Support

This image is built for multiple architectures:

- `linux/amd64` (x86_64)
- `linux/arm64` (ARM 64-bit)

The correct image is automatically pulled based on your system architecture.

## Security

### Rootless mode

Since Docker or Podman rootless modes already provide some protection, by mapping `root` inside the container to the user on the host, Kalanfa runs as `root` in the container. This should ensure that the files written to the `KALANFA_HOME` mount should match the user outside the container.

### Default rooted mode

The default installation modes for Docker and Podman align user IDs for `root` with the host's `root` user. This may not be ideal, especially for files written to the `KALANFA_HOME` mount point. Therefore, the entrypoint for the image:

- Switches to a non-root user (`kalanfa`)
- Attempts to match the `kalanfa` UID with the mount point
- Runs as root initially to perform necessary setup tasks (mount validation, file ownership)
- Privileges are dropped before starting the Kalanfa process using `gosu`

## Building Locally

```bash
docker build -t kalanfa:local \
  --build-arg KALANFA_VERSION_SPEC='==0.19.0' \
  -f Dockerfile .
```

## Troubleshooting

### Container Won't Start

If you see the error `ERROR: /kalanfa must be a mounted volume`, ensure you've added a volume mount.

```bash
# Wrong - no volume mount
docker run ghcr.io/learningequality/kalanfa:latest

# Correct - with volume mount
docker run -v /path/to/data:/kalanfa ghcr.io/learningequality/kalanfa:latest
```

### Permission Issues

If you encounter permission errors, ensure the mounted directory is writable by your host user (`myuser`):

```bash
chown -R myuser:myuser /path/to/data
```

## References

- [Kalanfa Documentation](https://kalanfa.readthedocs.io/)
- [Kalanfa GitHub Repository](https://github.com/learningequality/kalanfa)
- [Issue #14443](https://github.com/learningequality/kalanfa/issues/14443)
