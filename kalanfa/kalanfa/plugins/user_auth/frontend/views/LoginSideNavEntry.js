import { createTranslator } from 'kalanfa/utils/i18n';
import { UserKinds, NavComponentSections } from 'kalanfa/constants';
import { registerNavItem } from 'kalanfa/composables/useNav';
import urls from 'kalanfa/urls';

const navStrings = createTranslator('LoginSideNavEntryStrings', {
  signInLabel: {
    message: 'Sign in',
    context:
      "Users select the 'SIGN IN' button if they already have an account and a username in Kalanfa to get access to the platform.",
  },
});

registerNavItem({
  get url() {
    return urls['kalanfa:kalanfa.plugins.user_auth:user_auth']();
  },
  get label() {
    return navStrings.$tr('signInLabel');
  },
  icon: 'login',
  role: UserKinds.ANONYMOUS,
  section: NavComponentSections.ACCOUNT,
});
