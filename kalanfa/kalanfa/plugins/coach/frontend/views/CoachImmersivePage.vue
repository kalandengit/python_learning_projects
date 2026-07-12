<template>

  <NotificationsRoot
    :authorized="authorized"
    :authorizedRole="authorizedRole"
  >
    <ImmersivePage
      :appBarTitle="appBarTitle || defaultAppBarTitle"
      :icon="icon"
      :route="route"
      :primary="primary"
      :loading="loading"
      :appearanceOverrides="appearanceOverrides"
    >
      <div
        v-if="!loading"
        class="coach-main"
      >
        <slot></slot>
      </div>
    </ImmersivePage>
  </NotificationsRoot>

</template>


<script>

  import ImmersivePage from 'kalanfa/components/pages/ImmersivePage';
  import NotificationsRoot from 'kalanfa/components/pages/NotificationsRoot';
  import commonCoreStrings from 'kalanfa/uiText/commonCoreStrings';
  import { error } from 'kalanfa/utils/appError';
  import useCoreCoach from '../composables/useCoreCoach';

  export default {
    name: 'CoachImmersivePage',
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
    components: { ImmersivePage, NotificationsRoot },
    mixins: [commonCoreStrings],
    setup() {
      const { authorized, pageTitle, appBarTitle } = useCoreCoach();

      return {
        authorized,
        authorizedRole: 'adminOrCoach',
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
      appearanceOverrides: {
        type: Object,
        required: false,
        default: null,
      },
      icon: {
        type: String,
        default: 'close',
      },
      loading: {
        type: Boolean,
        default: null,
      },
      pageTitle: {
        type: String,
        default: null,
      },
      primary: {
        type: Boolean,
        required: false,
        default: true,
      },
      route: {
        type: Object,
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
