import { get } from '@vueuse/core';
import useUser from 'kalanfa/composables/useUser';
import redirectBrowser from 'kalanfa/utils/redirectBrowser';
import router from 'kalanfa/router';
import KalanfaApp from 'kalanfa-app';
import useFacility, { setSelectedFacilityId } from 'kalanfa-common/composables/useFacility';
import useFacilities from 'kalanfa-common/composables/useFacilities';
import { pageLoading } from 'kalanfa-common/composables/usePageLoading';
import { handleApiError } from 'kalanfa/utils/appError';
import RootVue from './views/FacilityIndex';
import routes from './routes';
import pluginModule from './modules/pluginModule';

class FacilityManagementModule extends KalanfaApp {
  get routes() {
    return routes;
  }
  get RootVue() {
    return RootVue;
  }
  get pluginModule() {
    return pluginModule;
  }
  ready() {
    const { isLearnerOnlyImport, isSuperuser } = useUser();
    const { facilities } = useFacilities();
    const { fetchFacility, fetchFacilities, fetchFacilityConfig } = useFacility();

    router.beforeEach(async (to, from, next) => {
      if (get(isLearnerOnlyImport)) {
        redirectBrowser();
        return;
      }

      pageLoading.value = true;

      setSelectedFacilityId(to.params.facility_id || null);

      try {
        if (facilities.value.length === 0) {
          if (get(isSuperuser)) {
            await fetchFacilities();
          } else {
            await fetchFacility();
          }
        }

        // always ensure updated config
        await fetchFacilityConfig();
      } catch (error) {
        handleApiError({ error, reloadOnReconnect: true });
      } finally {
        pageLoading.value = false;
        next();
      }
    });
    // reset module states after leaving their respective page
    router.afterEach((toRoute, fromRoute) => {
      this.store.dispatch('resetModuleState', { toRoute, fromRoute });
    });
    super.ready();
  }
}

export default new FacilityManagementModule();
