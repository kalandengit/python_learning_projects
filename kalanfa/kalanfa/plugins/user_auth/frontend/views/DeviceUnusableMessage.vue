<template>

  <div>
    <template v-if="reason === DeviceUnusableReason.NO_SUPERUSERS">
      <p>{{ strings.noSuperusersNotice$() }}</p>
      <p>{{ strings.noSuperuserCallToAction$() }}</p>
    </template>
    <template v-else-if="reason === DeviceUnusableReason.SUPERUSERS_SOFT_DELETED">
      <p>
        {{ strings.superusersSoftDeletedNotice$() }}
      </p>
      <p>
        {{ strings.superusersSoftDeletedCallToAction$() }}
      </p>
    </template>
    <p v-else>{{ strings.unknownIssueNotice$() }}</p>
    <KButton
      :disabled="taskLoading"
      style="margin-top: 16px"
      primary
      :text="strings.reinstallKalanfaAction$()"
      @click="deprovision"
    />
  </div>

</template>


<script>

  import TaskResource from 'kalanfa/apiResources/TaskResource';
  import useTaskPolling from 'kalanfa-common/composables/useTaskPolling';
  import useSnackbar from 'kalanfa/composables/useSnackbar';
  import { TaskStatuses, TaskTypes } from 'kalanfa-common/utils/syncTaskUtils';
  import redirectBrowser from 'kalanfa/utils/redirectBrowser';
  import { createTranslator } from 'kalanfa/utils/i18n';

  import { computed, ref, watch } from 'vue';
  import { DeviceUnusableReason } from '../constants';

  const DEPROVISION_TASK_QUEUE = 'device_deprovision';

  const strings = createTranslator('DeviceUnusableStrings', {
    noSuperusersNotice: {
      message: 'This device is unusable because there are no superuser accounts on this device.',
      context: 'Notice that there are no superuser accounts on the device',
    },
    noSuperuserCallToAction: {
      message: 'Please reinstall Kalanfa to create a superuser account.',
      context: 'Call to action to reinstall Kalanfa to create a superuser account',
    },
    superusersSoftDeletedNotice: {
      message:
        'This device is unusable because all superuser accounts on this device have been deleted on the server.',
      context: 'Notice that all superuser accounts have been deleted on the server',
    },
    superusersSoftDeletedCallToAction: {
      message:
        'Please contact your system administrator to restore your account or reinstall Kalanfa to create a new superuser account.',
      context:
        'Call to action to contact system administrator or reinstall Kalanfa to create a new superuser account',
    },
    unknownIssueNotice: {
      message: 'This device is unusable due to an unknown reason. Please contact support.',
      context: 'Notice that the device is unusable due to an unknown reason',
    },
    reinstallKalanfaAction: {
      message: 'Reinstall Kalanfa',
      context: 'Button text to reinstall Kalanfa',
    },
    deprovisioningError: {
      message: 'An error occurred while trying to reinstall Kalanfa. Please try again.',
      context: 'Error message when there is an error deprovisioning the device',
    },
  });

  export default {
    name: 'DeviceUnusableMessage',
    setup() {
      const taskLoading = ref(false);
      const { tasks } = useTaskPolling(DEPROVISION_TASK_QUEUE);
      const { createSnackbar } = useSnackbar();
      const deprovisionTask = computed(() => tasks.value[tasks.value.length - 1]);

      const deprovision = async () => {
        try {
          taskLoading.value = true;
          await TaskResource.startTask({
            type: TaskTypes.DEPROVISIONDEVICE,
          });
        } catch (e) {
          createSnackbar(strings.deprovisioningError$());
        }
      };

      const clearTasks = async () => {
        try {
          await TaskResource.clearAll(DEPROVISION_TASK_QUEUE);
        } catch (e) {
          return;
        }
      };

      watch(deprovisionTask, task => {
        if (!task) return;
        taskLoading.value = true;
        if (task.status === TaskStatuses.FAILED) {
          taskLoading.value = false;
          createSnackbar(strings.deprovisioningError$());
          clearTasks();
          return;
        }
        if (task.status === TaskStatuses.COMPLETED) {
          clearTasks();
          redirectBrowser();
        }
      });

      return {
        strings,
        taskLoading,
        DeviceUnusableReason,
        deprovision,
      };
    },
    props: {
      reason: {
        type: String,
        required: true,
        validator: value => Object.values(DeviceUnusableReason).includes(value),
      },
    },
  };

</script>
