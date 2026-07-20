import router from 'kalanfa/router';
import KalanfaApp from 'kalanfa-app';
import routes from './routes';
import pluginModule from './modules/pluginModule';

class UserProfileModule extends KalanfaApp {
  get routes() {
    return routes;
  }
  get pluginModule() {
    return pluginModule;
  }
  ready() {
    router.afterEach((toRoute, fromRoute) => {
      this.store.dispatch('resetModuleState', { toRoute, fromRoute });
    });
    super.ready();
  }
}

export default new UserProfileModule();
