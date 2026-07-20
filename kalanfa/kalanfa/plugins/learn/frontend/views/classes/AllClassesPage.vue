<template>

  <LearnAppBarPage
    :appBarTitle="learnString('learnLabel')"
    :loading="pageLoading"
  >
    <KBreadcrumbs
      :items="breadcrumbs"
      :ariaLabel="learnString('classesAndAssignmentsLabel')"
    />
    <YourClasses
      v-if="isUserLoggedIn"
      :classes="classrooms"
      :loading="pageLoading"
    />
    <AuthMessage
      v-else
      authorizedRole="learner"
    />
  </LearnAppBarPage>

</template>


<script>

  import { mapState } from 'vuex';
  import KBreadcrumbs from 'kalanfa-design-system/lib/KBreadcrumbs';
  import AuthMessage from 'kalanfa/components/AuthMessage';
  import commonCoreStrings from 'kalanfa/uiText/commonCoreStrings';
  import useUser from 'kalanfa/composables/useUser';
  import { pageLoading } from 'kalanfa-common/composables/usePageLoading';
  import YourClasses from '../YourClasses';
  import { PageNames } from '../../constants';
  import commonLearnStrings from '../commonLearnStrings';
  import LearnAppBarPage from '../LearnAppBarPage';

  export default {
    name: 'AllClassesPage',
    metaInfo() {
      return {
        title: this.coreString('classesLabel'),
      };
    },
    components: {
      KBreadcrumbs,
      AuthMessage,
      YourClasses,
      LearnAppBarPage,
    },
    mixins: [commonCoreStrings, commonLearnStrings],
    setup() {
      const { isUserLoggedIn } = useUser();
      return {
        isUserLoggedIn,
        pageLoading,
      };
    },
    computed: {
      ...mapState('classes', ['classrooms']),
      breadcrumbs() {
        return [
          {
            text: this.coreString('homeLabel'),
            link: { name: PageNames.HOME },
          },
          {
            text: this.coreString('classesLabel'),
          },
        ];
      },
    },
  };

</script>


<style lang="scss" scoped></style>
