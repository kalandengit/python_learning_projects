.. _Frontend build pipeline:

Frontend build pipeline
=======================

Asset pipelining is done using Webpack - this allows the use of require to import modules - as such all written code should be highly modular, individual files should be responsible for exporting a single function or object.

There are two distinct entities that control this behaviour - a Kalanfa Hook on the Python side, which manages the registration of the frontend code within Django and a ``buildConfig.js`` file for the webpack configuration. The format of the ``buildConfig.js`` is relatively straight forward, and the Kalanfa Hook and the ``buildConfig.js`` are connected by a single shared ``bundle_id`` specified in both:

.. code-block:: python

  @register_hook
  class LearnNavItem(NavigationHook):
      bundle_id = "side_nav"


  @register_hook
  class LearnAsset(webpack_hooks.WebpackBundleHook):
      bundle_id = "app"

.. code-block:: javascript

  module.exports = [
    {
      bundle_id: 'app',
      webpack_config: {
        entry: './frontend/app.js',
      },
    },
    {
      bundle_id: 'side_nav',
      webpack_config: {
        entry: './frontend/views/LearnSideNavEntry.vue',
      },
    },
  ];

The two specifications are connected by the shared specification of the ``bundle_id``. Minimally an ``entry`` value for the ``webpack_config`` object is required, but any other valid webpack configuration options may be passed as part of the object - they will be merged with the default Kalanfa webpack build.

Kalanfa has a system for synchronously and asynchronously loading these bundled JavaScript modules which is mediated by a small core JavaScript app, ``kalanfaCoreAppGlobal``. Kalanfa Modules define to which events they subscribe, and asynchronously registered Kalanfa Modules are loaded by ``kalanfaCoreAppGlobal`` only when those events are triggered. For example if the Video Viewer's Kalanfa Module subscribes to the *content_loaded:video* event, then when that event is triggered on ``kalanfaCoreAppGlobal`` it will asynchronously load the Video Viewer module and re-trigger the *content_loaded:video* event on the object the module returns.

Synchronous and asynchronous loading is defined by the template tag used to import the JavaScript for the Kalanfa Module into the Django template. Synchronous loading merely inserts the JavaScript and CSS for the Kalanfa Module directly into the Django template, meaning it is executed at page load.

This can be achieved in two ways using template tags.

The first way is simply by using the ``webpack_asset`` template tag defined in *kalanfa/core/webpack/templatetags/webpack_tags.py*.

The second way is if a Kalanfa Module needs to load in the template defined by another plugin or a core part of Kalanfa, a template tag and hook can be defined to register that Kalanfa Module's assets to be loaded on that page. An example of this is found in the ``base.html`` template using the ``frontend_base_assets`` tag, the hook that the template tag uses is defined in *kalanfa/core/hooks.py*.

Asynchronous loading can also, analogously, be done in two ways. Asynchronous loading registers a Kalanfa Module against ``kalanfaCoreAppGlobal`` on the frontend at page load, but does not load, or execute any of the code until the events that the Kalanfa Module specifies are triggered. When these are triggered, the ``kalanfaCoreAppGlobal`` will load the Kalanfa Module and pass on any callbacks once it has initialized. Asynchronous loading can be done either explicitly with a template tag that directly imports a single Kalanfa Module using ``webpack_base_async_assets``.


For some parts of the build system, we pre-build assets and commit them to the repository, when we essentially vendoring a built version of an external library. We do this for both the Khan Academy Perseus renderer, which we build a version of and commit to the repository, and the H5P Javascript files. Both have their own build processes that configured within the pnpm workspaces for each.

The Perseus build currently draws from the `Learning Equality fork of the Perseus repository <https://github.com/learningequality/perseus>`__ here we have made specific updates to Perseus, as it is no longer open sourced by Khan Academy. We have also made some edits and updates that make our build process easier and more streamlined. To run the build process to rebuild perseus dist bundle from the head of the default branch of our fork, run ``pnpm --filter kalanfa-perseus-viewer run build-perseus``. This will update all the relevant files and leave a diff to commit after it has finished. This should be committed and submitted as a pull request to update the code.
