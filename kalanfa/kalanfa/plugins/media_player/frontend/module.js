import store from 'kalanfa/store';
import ContentViewerModule from 'kalanfa-viewer';
import MediaPlayerComponent from './views/MediaPlayerIndex';
import storeModule from './modules';

class MediaPlayerModule extends ContentViewerModule {
  get viewerComponent() {
    return MediaPlayerComponent;
  }

  get store() {
    return store;
  }

  ready() {
    this.store.registerModule('mediaPlayer', storeModule);
  }
}

const mediaPlayerModule = new MediaPlayerModule();

export { mediaPlayerModule as default };
