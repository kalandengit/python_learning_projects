import { createTranslator } from 'kalanfa/utils/i18n';
import { UserKinds, NavComponentSections } from 'kalanfa/constants';
import { registerNavItem } from 'kalanfa/composables/useNav';
import urls from 'kalanfa/urls';

const navStrings = createTranslator('UserProfileSideNavEntryStrings', {
  profileLabel: {
    message: 'Profile',
    context: "Users can access and edit their personal details via the 'profile' option.",
  },
});

registerNavItem({
  get url() {
    return urls['kalanfa:kalanfa.plugins.user_profile:user_profile']();
  },
  get label() {
    return navStrings.$tr('profileLabel');
  },
  icon: 'person',
  role: UserKinds.LEARNER,
  section: NavComponentSections.ACCOUNT,
});
