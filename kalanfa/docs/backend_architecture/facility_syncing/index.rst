Learning facility data syncing
==============================

Kalanfa features the capability to synchronize facility data between Kalanfa instances, which supports its hybrid, distance, and offline learning applications. Each Kalanfa instance is able to sync partitioned datasets (a learning facility) in a peer-to-peer manner. To enable this functionality, Learning Equality developed a pure python database replication engine for Django, called Morango (`repository <https://github.com/learningequality/morango>`_, `documentation <https://morango.readthedocs.io/en/latest/>`_). Morango has several important features:

* A certificate-based authentication system to protect privacy and integrity of data
* A change-tracking system to support calculation of differences between databases across low-bandwidth connections
* A set of constructs to support data partitioning

The auth module found in ``kalanfa/core/auth`` contains most of the Kalanfa specific code that powers this feature.

The ``sync`` management command
-------------------------------
The ``sync`` management command inside the auth module uses Morango's tooling to manage facility syncs between itself and other Kalanfa devices, as well as Kalanfa Data Portal.

Integrating with a sync
---------------------------
There are two primary ways in which Kalanfa plugins may integrate with a sync:

a) Adding a Morango sync operation, which may execute at any stage of a sync
b) Adding a hook functions, which may execute before or after a sync transfer

When considering these two options, you should consider the following:

a) If the integration is vital to features being developed, a Morango sync operation should be implemented. This brings the benefit of providing integrity with the corresponding synced data, such that both are atomically applied.
b) If the integration isn't vital and is fail-tolerant, a sync hook function is the ideal choice as their execution does not impede the sync in any way.

Morango sync operations
---------------------------
A Morango operation is can be injected into any stage of a sync transfer, which include the following: ``INITIALIZING``, ``SERIALIZING``, ``QUEUING``, ``TRANSFERRING``, ``DEQUEUING``, ``DESERIALIZING``, and ``CLEANUP``. Morango uses Django settings to manage which operations occur during each stage, but Kalanfa builds upon by specifying one ``KalanfaSyncOperation`` (`code <https://github.com/learningequality/kalanfa/blob/d2ea094bf9532ed1d7eec5ee1e16203c67a74b6d/kalanfa/core/auth/sync_operations.py#L22>`_) that invokes each operation registered by Kalanfa plugins.

Here's an example of a Kalanfa plugin adding a custom sync operations:

.. code-block:: python

  from morango.sync.operations import LocalOperation

  from kalanfa.core.auth.hooks import FacilityDataSyncHook
  from kalanfa.core.auth.sync_operations import KalanfaSyncOperationMixin
  from kalanfa.plugins.hooks import register_hook


  class CustomCleanupOperation(KalanfaSyncOperationMixin, LocalOperation):
      priority = 5

      def handle_initial(self, context):
          """
          :type context: morango.sync.context.LocalSessionContext
          """
          # CUSTOM CODE HERE

  @register_hook
  class MyPluginSyncHook(FacilityDataSyncHook):
      cleanup_operations = [CustomCleanupOperation()]


Sync hook functions
-------------------
Sync hook functions utilize the same class as above, ``FacilityDataSyncHook``, but instead may defined ``pre_transfer`` or ``post_transfer`` methods.

Here's an example of a Kalanfa plugin adding a custom hooks:

.. code-block:: python

  from kalanfa.core.auth.hooks import FacilityDataSyncHook
  from kalanfa.plugins.hooks import register_hook

  @register_hook
  class MyPluginSyncHook(FacilityDataSyncHook):
      def pre_transfer(
          self,
          dataset_id,
          local_is_single_user,
          remote_is_single_user,
          single_user_id,
          context,
      ):
          """
          Invoked before the initialization stage
          :type dataset_id: str
          :type local_is_single_user: bool
          :type remote_is_single_user: bool
          :type single_user_id: str
          :type context: morango.sync.context.LocalSessionContext
          """
          # CUSTOM CODE HERE

      def post_transfer(
          self,
          dataset_id,
          local_is_single_user,
          remote_is_single_user,
          single_user_id,
          context,
      ):
          """
          Invoked at after the cleanup stage
          :type dataset_id: str
          :type local_is_single_user: bool
          :type remote_is_single_user: bool
          :type single_user_id: str
          :type context: morango.sync.context.LocalSessionContext
          """
          # CUSTOM CODE HERE
