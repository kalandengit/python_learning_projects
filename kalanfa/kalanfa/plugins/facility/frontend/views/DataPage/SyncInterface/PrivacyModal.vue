<template>

  <KModal
    :title="$tr('syncToKDP')"
    :submitText="coreString('closeAction')"
    size="medium"
    @cancel="closeModal"
    @submit="closeModal"
  >
    {{ $tr('privacyText') }}
  </KModal>

</template>


<script>

  import commonCoreStrings from 'kalanfa/uiText/commonCoreStrings';

  export default {
    name: 'PrivacyModal',
    mixins: [commonCoreStrings],
    methods: {
      closeModal() {
        this.$emit('cancel');
      },
    },
    $trs: {
      syncToKDP: {
        message: 'Kalanfa Data Portal',
        context:
          'If the Kalanfa facility is part of a larger organization that tracks data on the Kalanfa Data Portal, the user receives a project token to sync the facility data with servers operated by Learning Equality in the cloud.',
      },
      privacyText: {
        message:
          'By syncing this facility with the Kalanfa Data Portal, you are granting access to your data to organization admins on Kalanfa Data Portal. It will be uploaded to cloud servers operated by Learning Equality, who will also have access to this data.',
        context:
          "Text description on the 'Usage and privacy' pop-up window in the Facility > Data section.\n",
      },
    },
  };

</script>


<style lang="scss" scoped>

  @import '~kalanfa-design-system/lib/styles/definitions';

</style>
