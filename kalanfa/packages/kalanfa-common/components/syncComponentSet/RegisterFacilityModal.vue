<template>

  <KModal :title="registerFacility.$tr('registerFacility')">
    <p>{{ $tr('enterToken') }}</p>
    <KTextbox
      v-model="token"
      type="text"
      :label="$tr('projectToken')"
      :autofocus="true"
      :invalid="invalid"
      :invalidText="$tr('invalidToken')"
      @input="invalid = false"
    />
    <template #actions>
      <KButton
        :text="coreString('cancelAction')"
        appearance="flat-button"
        class="kbuttons"
        @click="closeModal"
      />
      <KButton
        v-if="displaySkipOption"
        :text="skip.$tr('skipAction')"
        appearance="raised-button"
        class="kbuttons"
        @click="skipRegister"
      />
      <KButton
        :text="coreString('continueAction')"
        appearance="raised-button"
        primary
        :disabled="submitting || !token"
        @click="validateToken"
      />
    </template>
  </KModal>

</template>


<script>

  import commonCoreStrings from 'kalanfa/uiText/commonCoreStrings';
  import CatchErrors from 'kalanfa/utils/CatchErrors';
  import { ERROR_CONSTANTS } from 'kalanfa/constants';
  import { handleApiError } from 'kalanfa/utils/appError';
  import PortalResource from 'kalanfa-common/apiResources/PortalResource';
  import { crossComponentTranslator } from 'kalanfa/utils/i18n';
  import GettingStartedFormAlt from '../../../../kalanfa/plugins/setup_wizard/frontend/views/onboarding-forms/GettingStartedFormAlt';
  import ConfirmationRegisterModal from './ConfirmationRegisterModal';

  export default {
    name: 'RegisterFacilityModal',
    mixins: [commonCoreStrings],
    setup() {
      return { handleApiError };
    },
    props: {
      displaySkipOption: {
        type: Boolean,
        required: false,
        default: false,
      },
      facility: {
        type: Object,
        required: false,
        default: () => ({}),
      },
    },
    data() {
      return {
        submitting: false,
        token: null,
        invalid: false,
        registerFacility: crossComponentTranslator(ConfirmationRegisterModal),
        skip: crossComponentTranslator(GettingStartedFormAlt),
      };
    },
    methods: {
      closeModal() {
        this.$emit('cancel');
      },
      skipRegister() {
        this.$emit('skip', this.facility);
      },
      validateToken() {
        // TODO synchronously handle empty strings
        const strippedToken = this.token.replace('-', '');
        this.submitting = true;
        PortalResource.validateToken(strippedToken)
          .then(response => {
            this.submitting = false;
            this.$emit('success', {
              name: response.data.name,
              token: strippedToken,
            });
          })
          .catch(error => {
            const errorsCaught = CatchErrors(error, [
              ERROR_CONSTANTS.INVALID_KDP_REGISTRATION_TOKEN,
            ]);
            if (errorsCaught) {
              this.invalid = true;
              this.submitting = false;
            } else {
              this.handleApiError({ error });
            }
          });
      },
    },
    $trs: {
      enterToken: {
        message: 'Enter a project token from Kalanfa Data Portal',
        context:
          'If the Kalanfa facility is part of a larger organization that tracks data on the Kalanfa Data Portal, an admin may receive a project token to sync the facility data with the organization in the cloud.\n\nThis text is a prompt that appears on the Sync Facility Data screen where the admin would enter this project token.\n\nThe project token is usually composed of a short sequence of characters.',
      },
      projectToken: {
        message: 'Project token',
        context:
          'If the Kalanfa facility is part of a larger organization that tracks data on the Kalanfa Data Portal, the admin may receive a project token to sync the facility data with the organization in the cloud.\n\nThe project token is usually composed of a short sequence of characters.',
      },
      invalidToken: {
        message: 'Invalid token',
        context:
          "This is an error message that displays when an admin enters an incorrect project token on the 'Sync Facility Data' screen.\n\nThe project token is usually composed of a short sequence of characters.",
      },
    },
  };

</script>


<style lang="scss" scoped>

  @import '~kalanfa-design-system/lib/styles/definitions';

  .kbuttons {
    margin-right: 10px;
  }

</style>
