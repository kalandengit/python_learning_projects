import KalanfaApp from 'kalanfa-app';
import routes from './routes';
import pluginModule from './modules/pluginModule';

class PoliciesModule extends KalanfaApp {
  get routes() {
    return routes;
  }
  get pluginModule() {
    return pluginModule;
  }
  ready() {
    super.ready();
  }
}

export default new PoliciesModule();
