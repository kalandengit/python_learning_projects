
Kalanfa Sentry Plugin
======================


How can I install this plugin?
------------------------------

1. Inside your Kalanfa virtual environment:
    ``pip install kalanfa-sentry-plugin``

2. Activate the plugin:

    ``kalanfa plugin enable kalanfa_sentry_plugin``

3. Restart Kalanfa.

How can I install this plugin for development?
------------------------------------------------

1. From the root of the ``kalanfa`` monorepo, install the Python and frontend dependencies:

    ``uv sync --all-packages``

    ``uvx prek install``

    ``pnpm install``

2. Activate the plugin:

    ``KALANFA_HOME="$(pwd)/.kalanfa" uv run kalanfa plugin enable kalanfa_sentry_plugin``


How to publish to PyPi?
------------------------------

Publishing is automated by the ``pypi_packages_publish.yml`` GitHub Actions workflow.

- It lives in the monorepo root's ``.github/workflows/`` directory.
- It runs when this plugin's ``pyproject.toml`` version is bumped.
