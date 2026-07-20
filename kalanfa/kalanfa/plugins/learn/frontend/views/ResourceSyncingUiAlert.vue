<template>

  <MissingResourceAlert :multiple="multiple">
    <template
      v-if="isLearnerOnlyImport && isSyncing"
      #syncAlert
    >
      {{ syncMessage }}
    </template>
  </MissingResourceAlert>

</template>


<script>

  import { get } from '@vueuse/core';
  import { computed, watch } from 'vue';
  import MissingResourceAlert from 'kalanfa-common/components/MissingResourceAlert.vue';
  import useUserSyncStatus from 'kalanfa/composables/useUserSyncStatus';
  import { SyncStatus } from 'kalanfa/constants';
  import { createTranslator } from 'kalanfa/utils/i18n';
  import useUser from 'kalanfa/composables/useUser';

  const syncStatusDescriptionStrings = createTranslator('SyncStatusDescription', {
    syncingDescription: {
      message: 'The device is currently syncing.',
      context: 'Description of the device syncing status.',
    },
    queuedDescription: {
      message: 'The device is waiting to sync.',
      context: 'Description of the device syncing status',
    },
  });

  export default {
    name: 'ResourceSyncingUiAlert',
    components: {
      MissingResourceAlert,
    },
    setup(props, { emit }) {
      const { status, syncDownloadsInProgress } = useUserSyncStatus();
      const { isLearnerOnlyImport } = useUser();
      const isSyncing = computed(() => {
        return (
          get(status) === SyncStatus.QUEUED ||
          get(status) === SyncStatus.SYNCING ||
          get(syncDownloadsInProgress)
        );
      });

      watch(isSyncing, (newVal, oldVal) => {
        if (newVal === false && oldVal === true) {
          emit('syncComplete');
        }
      });

      return {
        status,
        isLearnerOnlyImport,
        isSyncing,
      };
    },
    props: {
      multiple: {
        type: Boolean,
        default: true,
      },
    },
    computed: {
      syncMessage() {
        /* eslint-disable kalanfa/vue-no-undefined-string-uses */
        return this.status == SyncStatus.QUEUED
          ? syncStatusDescriptionStrings.$tr('queuedDescription')
          : syncStatusDescriptionStrings.$tr('syncingDescription');
        /* eslint-enable */
      },
    },
  };

</script>
