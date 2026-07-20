<template>

  <KModal
    :title="coreString('removeFromLibrary')"
    :submitText="coreString('removeAction')"
    :cancelText="coreString('cancelAction')"
    @submit="removeResources"
    @cancel="$emit('cancel')"
  >
    {{ message }}
  </KModal>

</template>


<script>

  import commonCoreStrings from 'kalanfa/uiText/commonCoreStrings';

  export default {
    name: 'ConfirmationDeleteModal',
    mixins: [commonCoreStrings],
    props: {
      resourcesToDelete: {
        type: Array,
        required: true,
      },
    },
    computed: {
      message() {
        if (this.resourcesToDelete.length === 1) {
          return this.coreString('removeResourceText');
        }
        return this.coreString('removeResourcesText');
      },
    },
    methods: {
      removeResources() {
        this.$emit('success');
      },
    },
  };

</script>


<style lang="scss" scoped>

  @import '~kalanfa-design-system/lib/styles/definitions';

</style>
