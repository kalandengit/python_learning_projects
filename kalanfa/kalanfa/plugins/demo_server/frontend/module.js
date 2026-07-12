import KalanfaModule from 'kalanfa-module';
import DemoServerBannerContent from './DemoServerBannerContent';

class DemoServerModule extends KalanfaModule {
  ready() {
    if (!window._coreBannerContent) {
      window._coreBannerContent = [];
    }
    window._coreBannerContent.push(DemoServerBannerContent);
  }
}

export default new DemoServerModule();
