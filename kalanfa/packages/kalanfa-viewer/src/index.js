import KalanfaModule from 'kalanfa-module';

export default class ContentViewer extends KalanfaModule {
  get viewerComponent() {
    return null;
  }
  loadDirectionalCSS(direction) {
    return this.Kalanfa.loadDirectionalCSS(this, direction);
  }
}
