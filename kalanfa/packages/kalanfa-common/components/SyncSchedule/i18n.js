import { createTranslator } from 'kalanfa/utils/i18n';

// Taken from the PrivacyModal component in the facility plugin.
export const kdpNameTranslator = createTranslator('PrivacyModal', {
  syncToKDP: {
    message: 'Kalanfa Data Portal',
    context:
      'If the Kalanfa facility is part of a larger organization that tracks data on the Kalanfa Data Portal, the user receives a project token to sync the facility data with servers operated by Learning Equality in the cloud.',
  },
});
