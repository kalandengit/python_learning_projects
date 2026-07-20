<template>

  <SelectSourceModal
    :submitDisabled="formIsDisabled"
    :showLoadingMessage="formIsDisabled && !initialDelay"
    @submit="handleSubmit"
    @cancel="handleCancel"
  >
    <KRadioButtonGroup>
      <KRadioButton
        v-model="source"
        :label="$tr('network')"
        :buttonValue="ContentSources.KALANFA_STUDIO"
        :disabled="kalanfaStudioIsOffline || formIsDisabled"
        :autofocus="!kalanfaStudioIsOffline"
        :description="$tr('studioDescription')"
      />
      <KRadioButton
        v-model="source"
        :label="$tr('localNetworkOrInternet')"
        :buttonValue="ContentSources.PEER_KALANFA_SERVER"
        :disabled="formIsDisabled"
        :description="$tr('networkDescription')"
      />
      <KRadioButton
        v-model="source"
        :label="$tr('localDrives')"
        :buttonValue="ContentSources.LOCAL_DRIVE"
        :disabled="formIsDisabled"
        :description="$tr('localDescription')"
      />
    </KRadioButtonGroup>
  </SelectSourceModal>

</template>


<script>

  import { mapActions, mapMutations } from 'vuex';
  import RemoteChannelResource from 'kalanfa-common/apiResources/RemoteChannelResource';
  import SelectSourceModal from 'kalanfa-common/components/syncComponentSet/SelectSourceModal';
  import { ContentSources } from '../../../constants';

  export default {
    name: 'SelectImportSourceModal',
    components: {
      SelectSourceModal,
    },
    data() {
      return {
        source: ContentSources.KALANFA_STUDIO,
        initialDelay: true, // hide everything for a second to prevent flicker
        formIsDisabled: true,
        kalanfaStudioIsOffline: false,
        ContentSources,
      };
    },
    created() {
      setTimeout(() => {
        this.initialDelay = false;
      }, 1000);
      RemoteChannelResource.getKalanfaStudioStatus().then(({ data }) => {
        if (data.status === 'offline') {
          this.source = ContentSources.PEER_KALANFA_SERVER;
          this.kalanfaStudioIsOffline = true;
        }
        this.formIsDisabled = false;
      });
    },
    methods: {
      ...mapActions('manageContent/wizard', ['goForwardFromSelectImportSourceModal']),
      ...mapMutations('manageContent/wizard', {
        resetContentWizardState: 'RESET_STATE',
      }),
      handleSubmit() {
        if (!this.formIsDisabled) {
          if (this.$attrs.manageMode) {
            this.$emit('submit', { source: this.source });
          } else {
            this.goForwardFromSelectImportSourceModal(this.source);
          }
        }
      },
      handleCancel() {
        if (this.$attrs.manageMode) {
          this.$emit('cancel');
        } else {
          this.resetContentWizardState();
        }
      },
    },
    $trs: {
      network: {
        message: 'Kalanfa Studio (online)',
        context: 'Refers to a source where resources can be imported from.\n',
      },
      localNetworkOrInternet: {
        message: 'Local network or internet',
        context: 'Refers to a source where resources can be imported from.',
      },
      localDrives: {
        message: 'Attached drive or memory card',
        context: 'Refers to a source where resources can be imported from.',
      },
      studioDescription: {
        message: 'Import resources from Kalanfa Studio if you are connected to the internet',
        context: 'Description referring to importing channels from Kalanfa Studio.',
      },
      networkDescription: {
        message:
          'Import resources from another Kalanfa server running on a device on your local network or the internet',
        context:
          'Description referring to importing channels from a local network or the internet.',
      },
      localDescription: {
        message:
          'Import resources from a drive. Channels must have first been exported onto the drive from another Kalanfa server',
        context:
          'Description referring to importing channels from an attached drive or memory card.',
      },
    },
  };

</script>


<style lang="scss" scoped></style>
