<template>

  <NotificationsRoot
    :authorized="authorized"
    :authorizedRole="authorizedRole"
  >
    <AppBarPage
      :title="appBarTitle || defaultAppBarTitle"
      :showNavigation="Boolean(classId)"
      :loading="loading"
    >
      <div class="coach-main">
        <slot></slot>
      </div>
    </AppBarPage>
  </NotificationsRoot>

</template>


<script>

  import AppBarPage from 'kalanfa/components/pages/AppBarPage';
  import NotificationsRoot from 'kalanfa/components/pages/NotificationsRoot';
  import commonCoreStrings from 'kalanfa/uiText/commonCoreStrings';
  import { error } from 'kalanfa/utils/appError';
  import useCoreCoach from '../composables/useCoreCoach';

  export default {
    name: 'CoachAppBarPage',
    metaInfo() {
      return {
        // Use arrow function to bind $tr to this component
        titleTemplate: title => {
          if (this.error) {
            return this.$tr('kalanfaTitleMessage', { title: this.$tr('errorPageTitle') });
          }
          if (!title) {
            // If no child component sets title, it reads 'Kalanfa'
            return this.coreString('kalanfaLabel');
          }
          // If child component sets title, it reads 'Child Title - Kalanfa'
          return this.$tr('kalanfaTitleMessage', { title });
        },
        title: this.pageTitle || this.defaultPageTitle,
      };
    },
    components: { AppBarPage, NotificationsRoot },
    mixins: [commonCoreStrings],
    setup() {
      const { authorized, pageTitle, appBarTitle, classId } = useCoreCoach();

      return {
        authorized,
        authorizedRole: 'adminOrCoach',
        classId,
        defaultPageTitle: pageTitle,
        defaultAppBarTitle: appBarTitle,
        error,
      };
    },
    props: {
      appBarTitle: {
        type: String,
        default: null,
      },
      loading: {
        type: Boolean,
        default: false,
      },
      pageTitle: {
        type: String,
        default: null,
      },
    },
    $trs: {
      kalanfaTitleMessage: {
        message: '{ title } - Kalanfa',
        context: 'DO NOT TRANSLATE\nCopy the source string.',
      },
      errorPageTitle: {
        message: 'Error',
        context:
          "When Kalanfa throws an error, this is the text that's used as the title of the error page. The description of the error follows below.",
      },
    },
  };

</script>


<style lang="scss" scoped>

  .coach-main {
    margin: 0 auto;
  }

</style>
