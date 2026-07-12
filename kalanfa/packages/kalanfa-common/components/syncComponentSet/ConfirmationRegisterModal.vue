<template>

  <KModal
    :title="$tr('registerFacility')"
    :submitText="registerText"
    :cancelText="cancelText"
    @submit="registerFacility"
    @cancel="cancel"
  >
    <template v-if="!alreadyRegistered">
      <p>{{ $tr('registerWith', { name: projectName }) }}</p>
      <p>{{ $tr('dataSaved') }}</p>
    </template>

    <template v-else>
      {{ $tr('alreadyRegistered', { name: projectName }) }}
    </template>
  </KModal>

</template>


<script>

  import commonCoreStrings from 'kalanfa/uiText/commonCoreStrings';
  import CatchErrors from 'kalanfa/utils/CatchErrors';
  import { ERROR_CONSTANTS } from 'kalanfa/constants';
  import { handleApiError } from 'kalanfa/utils/appError';
  import FacilityDatasetResource from 'kalanfa-common/apiResources/FacilityDatasetResource';
  import PortalResource from 'kalanfa-common/apiResources/PortalResource';

  export default {
    name: 'ConfirmationRegisterModal',
    mixins: [commonCoreStrings],
    setup() {
      return { handleApiError };
    },
    props: {
      projectName: {
        type: String,
        required: true,
      },
      targetFacility: {
        type: Object,
        required: true,
      },
      token: {
        type: String,
        required: true,
      },
      /**
       * Whether or not the modal should emit a success event
       * after the facility has been discovered to be already registered.
       */
      successOnAlreadyRegistered: {
        type: Boolean,
        required: false,
        default: false,
      },
    },
    data() {
      return {
        alreadyRegistered: false,
      };
    },
    computed: {
      cancelText() {
        return this.alreadyRegistered
          ? this.coreString('closeAction')
          : this.coreString('cancelAction');
      },
      registerText() {
        return this.alreadyRegistered ? null : this.coreString('registerAction');
      },
    },
    methods: {
      registerFacility() {
        this.submitting = true;
        PortalResource.registerFacility({
          facility_id: this.targetFacility.id,
          name: this.targetFacility.name,
          token: this.token,
        })
          .then(() => {
            FacilityDatasetResource.saveModel({
              id: this.targetFacility.dataset.id,
              data: { registered: true },
              exists: true,
            }).then(() => {
              this.$emit('success', this.targetFacility);
              this.submitting = false;
            });
          })
          .catch(error => {
            const errorsCaught = CatchErrors(error, [
              ERROR_CONSTANTS.ALREADY_REGISTERED_FOR_COMMUNITY,
            ]);
            if (errorsCaught) {
              this.submitting = false;
              this.alreadyRegistered = true;
            } else {
              this.handleApiError({ error });
            }
          });
      },
      cancel() {
        if (this.alreadyRegistered && this.successOnAlreadyRegistered) {
          this.$emit('success', this.targetFacility);
        } else {
          this.$emit('cancel');
        }
      },
    },
    $trs: {
      registerFacility: {
        message: 'Register facility',
        context: "An action that describes 'registering' a facility to the Kalanfa Data Portal.",
      },
      registerWith: {
        message: "Register with '{name}'?",
        context:
          'Kalanfa is asking for a confirmation before registering the facility with a project called {name}.',
      },
      dataSaved: {
        message: 'Data will be saved to the cloud',
        context:
          'Message indicating that facility data will be synced with the organization in the cloud.',
      },
      alreadyRegistered: {
        message: "Already registered with '{name}'",
        context:
          'Once a facility has been registered on the Kalanfa Data Portal, if admin makes a second attempt to register, Kalanfa will reply with this reminder that the facility has already been registered with a project called {name}.',
      },
    },
  };

</script>


<style lang="scss" scoped>

  @import '~kalanfa-design-system/lib/styles/definitions';

</style>
