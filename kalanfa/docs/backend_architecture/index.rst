Backend architecture
====================

.. warning::
   **API Stability Notice**

   Kalanfa has two types of API endpoints:

   **Internal APIs** (most endpoints): These are designed for Kalanfa's own frontend and
   may change without notice between releases. **Do not build external applications** that
   depend on these APIs. Breaking changes can and will occur as Kalanfa evolves.

   **Public APIs** (``/public/`` endpoints only): These endpoints under the ``/public/`` URL
   namespace are maintained with backwards compatibility for use by other Kalanfa instances
   and authorized integrations. See the public API documentation for details.

   When in doubt, assume an endpoint is internal unless explicitly documented as public.

.. toctree::
  :maxdepth: 1

  content/index
  uap/index
  logger/index
  plugins
  tasks
  api_patterns
  testing
  dist_build_pipeline
  upgrade
  facility_syncing/index
