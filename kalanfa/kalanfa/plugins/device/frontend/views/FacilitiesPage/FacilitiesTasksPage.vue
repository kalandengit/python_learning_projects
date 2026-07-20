<template>

  <ImmersivePage
    :appBarTitle="$tr('facilitiesTaskManagerTitle')"
    :route="backRoute"
    :loading="pageLoading"
  >
    <KPageContainer class="device-container">
      <HeaderWithOptions :headerText="coreString('tasksLabel')">
        <template #options>
          <KButton
            v-if="someClearableTasks"
            :text="getTaskString('clearCompletedTasksAction')"
            @click="handleClickClearAll"
          />
        </template>
      </HeaderWithOptions>

      <p v-if="facilityTasks.length === 0">
        {{ deviceString('emptyTasksMessage') }}
      </p>
      <div>
        <FacilityTaskPanel
          v-for="(task, idx) in activeFacilityTasks"
          :key="idx"
          class="task-panel"
          :style="{ borderBottomColor: $themePalette.grey.v_300 }"
          :task="task"
          @cancel="cancel(task)"
          @clear="clear(task)"
          @retry="retry(task)"
        />
      </div>
    </KPageContainer>
  </ImmersivePage>

</template>


<script>

  import TaskResource from 'kalanfa/apiResources/TaskResource';
  import FacilityTaskPanel from 'kalanfa-common/components/syncComponentSet/FacilityTaskPanel';
  import commonCoreStrings from 'kalanfa/uiText/commonCoreStrings';
  import commonTaskStrings from 'kalanfa-common/uiText/tasks';
  import commonSyncElements from 'kalanfa-common/mixins/commonSyncElements';
  import ImmersivePage from 'kalanfa/components/pages/ImmersivePage';
  import { pageLoading } from 'kalanfa-common/composables/usePageLoading';
  import HeaderWithOptions from '../HeaderWithOptions';
  import commonDeviceStrings from '../commonDeviceStrings';
  import { PageNames } from '../../constants';
  import facilityTasksQueue from './facilityTasksQueue';

  export default {
    name: 'FacilitiesTasksPage',
    metaInfo() {
      return {
        title: this.coreString('tasksLabel'),
      };
    },
    components: {
      FacilityTaskPanel,
      HeaderWithOptions,
      ImmersivePage,
    },
    mixins: [
      commonCoreStrings,
      commonTaskStrings,
      commonSyncElements,
      facilityTasksQueue,
      commonDeviceStrings,
    ],
    setup() {
      return { pageLoading };
    },
    data() {
      return {
        // (facilityTasksQueue) facilityTasks
      };
    },
    computed: {
      backRoute() {
        return { name: PageNames.FACILITIES_PAGE };
      },
      someClearableTasks() {
        return Boolean(this.activeFacilityTasks.find(task => task.clearable));
      },
    },
    methods: {
      handleClickClearAll() {
        this.clearCompletedFacilityTasks();
      },
      cancel(task) {
        return TaskResource.cancel(task.id);
      },
      clear(task) {
        return TaskResource.clear(task.id);
      },
      retry(task) {
        return TaskResource.restart(task.id);
      },
    },
    $trs: {
      facilitiesTaskManagerTitle: {
        message: 'Facilities - Task manager',
        context: 'Title of the page that displays all the tasks in the task manager.',
      },
    },
  };

</script>


<style lang="scss" scoped>

  @import '../../styles/definitions';

  .device-container {
    @include device-kpagecontainer;
  }

  .buttons {
    margin: auto;
  }

  .task-panel {
    border-bottom: 1px solid;

    &:last-of-type {
      border-bottom-style: none;
    }
  }

</style>
