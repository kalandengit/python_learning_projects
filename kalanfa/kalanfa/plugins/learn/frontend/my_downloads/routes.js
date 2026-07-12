import redirectBrowser from 'kalanfa/utils/redirectBrowser';
import useUser from 'kalanfa/composables/useUser';
import { get } from '@vueuse/core';
import MyDownloadsPage from './views/MyDownloads';

export default [
  {
    path: '/',
    name: 'MY_DOWNLOADS',
    component: MyDownloadsPage,
    beforeEnter(to, from, next) {
      const { isUserLoggedIn } = useUser();
      if (!get(isUserLoggedIn)) {
        redirectBrowser();
      } else {
        next();
      }
    },
  },
];
