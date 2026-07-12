import redirectBrowser from 'kalanfa/utils/redirectBrowser';
import { availableLanguages, currentLanguage, sortLanguages } from 'kalanfa/utils/i18n';
import { httpClient } from 'kalanfa/client';
import urls from 'kalanfa/urls';

export default {
  methods: {
    switchLanguage(code) {
      const url = urls['kalanfa:core:set_language']();
      const data = { language: code, next: window.location.href };
      httpClient({
        method: 'POST',
        url,
        data,
      }).then(response => {
        // Endpoint returns a URL to redirect to.
        // Redirect to it.
        redirectBrowser(response.data);
      });
    },
  },
  computed: {
    languageOptions() {
      return sortLanguages(Object.values(availableLanguages), currentLanguage);
    },
  },
};
