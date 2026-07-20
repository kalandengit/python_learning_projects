import KalanfaApp from 'kalanfa-app';
import routes from './routes';
import pluginModule from './modules/pluginModule';

class MyDownloadsModule extends KalanfaApp {
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

export default new MyDownloadsModule();
