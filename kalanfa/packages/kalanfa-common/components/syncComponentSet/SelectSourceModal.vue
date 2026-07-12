<template>

  <KModal
    :title="getCommonSyncString('selectSourceTitle')"
    size="medium"
    :submitText="coreString('continueAction')"
    :cancelText="coreString('cancelAction')"
    :submitDisabled="submitDisabled"
    @submit="$emit('submit')"
    @cancel="$emit('cancel')"
  >
    <UiAlert
      v-if="showLoadingMessage"
      type="info"
      :dismissible="false"
    >
      {{ $tr('loadingMessage') }}
    </UiAlert>
    <slot></slot>
  </KModal>

</template>


<script>

  import UiAlert from 'kalanfa-design-system/lib/keen/UiAlert';
  import commonCoreStrings from 'kalanfa/uiText/commonCoreStrings';
  import commonSyncElements from 'kalanfa-common/mixins/commonSyncElements';

  // This is a SelectSourceModal template with the common heading and loading
  // message widget. Place the form (usually a radio button group)
  // inside the default slot.
  export default {
    name: 'SelectSourceModal',
    components: { UiAlert },
    mixins: [commonCoreStrings, commonSyncElements],
    props: {
      showLoadingMessage: {
        type: Boolean,
        default: false,
      },
      submitDisabled: {
        type: Boolean,
        required: true,
      },
    },
    $trs: {
      loadingMessage: {
        message: 'Loading connections…',
        context: 'Refers to loading connections to different sources.',
      },
    },
  };

</script>


<style lang="scss" scoped></style>
