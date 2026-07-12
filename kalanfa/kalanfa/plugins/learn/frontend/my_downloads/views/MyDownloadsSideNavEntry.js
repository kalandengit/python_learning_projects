import { createTranslator } from 'kalanfa/utils/i18n';
import { UserKinds, NavComponentSections } from 'kalanfa/constants';
import { registerNavItem } from 'kalanfa/composables/useNav';
import urls from 'kalanfa/urls';
import plugin_data from 'kalanfa-plugin-data';

const navStrings = createTranslator('MyDownloadsSideNavEntryStrings', {
  myDownloadsLabel: {
    message: 'My downloads',
    context: "Users can access and see their content downloads via 'my downloads' option.",
  },
});

if (plugin_data.allowLearnerDownloads) {
  registerNavItem({
    get url() {
      return urls['kalanfa:kalanfa.plugins.learn:my_downloads']();
    },
    get label() {
      return navStrings.$tr('myDownloadsLabel');
    },
    icon: 'download',
    role: UserKinds.LEARNER,
    section: NavComponentSections.ACCOUNT,
  });
}
