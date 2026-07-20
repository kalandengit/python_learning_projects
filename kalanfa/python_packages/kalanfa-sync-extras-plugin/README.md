# Kalanfa Sync Extras plugin

## What is this?

Kalanfa is a Learning Management System / Learning App designed to run on low-power devices, targeting the needs of learners and teachers in contexts with limited infrastructure. See [learningequality.org/kalanfa](https://learningequality.org/kalanfa/) for more info.

Kalanfa supports syncing facility data between two instances. This plugin provides additional sync related features that can be turned on to customize the behavior of those syncs. In particular, these features can enhance Kalanfa's syncing mechanism when dealing with a large database or dataset.


## How can I install this plugin?

1. Inside your Kalanfa virtual environment: `pip install kalanfa-sync-extras-plugin`

2. Activate the plugin: `kalanfa plugin enable kalanfa_sync_extras_plugin`

3. Restart Kalanfa


## Plugin configuration

The following configuration options are available, and should be defined within the `[Sync]` section of `$KALANFA_HOME/options.ini` or define environment variables with the prefix `KALANFA_SYNC_`.

| Option                             | Type | Default                           | Description                                                                  |
|------------------------------------| --- |-----------------------------------|------------------------------------------------------------------------------|
| `BACKGROUND_INITIALIZATION`        | Boolean | `False`                           | Whether to enable background initialization of pull syncs                    |
| `BACKGROUND_INITIALIZATION_STAGES` | String | `serializing,queuing`                    | Comma separated list of stages for which to enable background initialization |
| `BACKGROUND_FINALIZATION`          | Boolean | `False`                           | Whether to enable background finalization of push syncs                      |
| `BACKGROUND_FINALIZATION_STAGES`   | String | `dequeuing,deserializing,cleanup` | Comma separated list of stages for which to enable background finalization   |

### Example
```ini
[Sync]
BACKGROUND_INITIALIZATION = True
BACKGROUND_INITIALIZATION_STAGES = "serializing"
BACKGROUND_FINALIZATION = True
BACKGROUND_FINALIZATION_STAGES = "deserializing,cleanup"
```

## Development
### Getting started
```bash
$ uv sync --all-packages
$ uvx prek install
$ KALANFA_HOME="$(pwd)/.kalanfa" uv run kalanfa plugin enable kalanfa_sync_extras_plugin
```

Run these from this directory. `--all-packages` is required; otherwise the
shared venv drops root Kalanfa's own runtime dependencies (Django, Click, etc.).

## Testing
### Getting started
```bash
$ uv sync --group test --all-packages
$ KALANFA_HOME="$(pwd)/.kalanfa" uv run kalanfa plugin enable kalanfa_sync_extras_plugin
```

### Running them
```bash
$ pytest test/
```
