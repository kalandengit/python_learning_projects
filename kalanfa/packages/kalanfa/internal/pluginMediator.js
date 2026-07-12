import Vue from 'vue';
import logging from 'kalanfa-logging';
import scriptLoader from 'kalanfa/utils/scriptLoader';
import { VIEWER_SUFFIX } from 'kalanfa/constants';
import { languageDirections, currentLanguage } from 'kalanfa/utils/i18n';
import { rtlManager } from 'kalanfa/rtlcss';
import ContentViewerLoading from '../components/internal/ContentViewer/ContentViewerLoading';
import ContentViewerError from '../components/internal/ContentViewer/ContentViewerError';

/**
 * @typedef {import('kalanfa-module').default} KalanfaModule
 */

const logger = logging.getLogger(__filename);

/**
 * Array containing the names of all methods of the Mediator that
 * should be exposed publicly through the Facade.
 * @type {string[]}
 */
const publicMethods = [
  'registerKalanfaModuleSync',
  'registerLanguageAssets',
  'registerContentViewer',
  'loadDirectionalCSS',
  'ready',
];

const domParser = new DOMParser();

/*
 * JSON data that we read from Django have been passed through
 * Django's marksafe function that escapes any HTML characters.
 * Use the DOMParser to decode these before we read parse the JSON.
 */
function decodeMarkedSafeText(text) {
  const dom = domParser.parseFromString(text, 'text/html');
  return dom.documentElement.textContent;
}

export default function pluginMediatorFactory(facade) {
  /**
   * The Mediator object - registers and loads kalanfa_modules.
   */
  const mediator = {
    /**
     * Keep track of all registered kalanfa_modules - object is of form:
     * kalanfaModuleName: kalanfa_module_object
     */
    _kalanfaModuleRegistry: {},

    // wait to call kalanfa_module `ready` until dependencies are loaded
    _ready: false,

    /**
     * Callbacks to invoke when the mediator becomes ready. Accumulated via
     * registerKalanfaModuleSync() when _ready is false; flushed by setReady().
     * @type {Function[]}
     */
    _readyCallbacks: [],

    /**
     * Map from kalanfaModule name to an array of pending callbacks. Callbacks
     * are queued in retrieveContentViewer() when the module has not yet
     * registered; flushed and removed in registerKalanfaModuleSync().
     * @type {{[key: string]: Function[]}}
     */
    _contentViewerCallbacks: {},

    /**
     * Keep track of all registered language assets for modules.
     * kalanfaModuleName: {object} - with keys for different languages.
     */
    _languageAssetRegistry: {},

    /**
     * Keep track of all registered content viewers.
     */
    _contentViewerRegistry: {},
    /**
     * Keep track of urls for content viewers.
     */
    _contentViewerUrls: {},
    /**
     * Public ready method - called when plugins can start operating
     */
    ready() {
      this.registerMessages();
      this.registerAllContentViewers();
      this.setReady();
    },

    /**
     * Mark the mediator as ready and flush all pending ready callbacks.
     */
    setReady() {
      this._ready = true;
      this._readyCallbacks.splice(0).forEach(cb => cb());
    },

    /**
     * Registers a kalanfaModule that has already been loaded into the
     * frontend. Flushes any pending content viewer callbacks for the module, then
     * calls kalanfaModule.ready() immediately if the mediator is ready, or defers it
     * until setReady() is called.
     * @param {KalanfaModule} kalanfaModule - The freshly loaded module instance to register
     */
    registerKalanfaModuleSync(kalanfaModule) {
      this._kalanfaModuleRegistry[kalanfaModule.name] = kalanfaModule;

      logger.info(`Kalanfa Modules: ${kalanfaModule.name} registered`);

      const callbacks = this._contentViewerCallbacks[kalanfaModule.name];
      if (callbacks) {
        callbacks.forEach(cb => cb(kalanfaModule));
        delete this._contentViewerCallbacks[kalanfaModule.name];
      }

      if (this._ready) {
        kalanfaModule.ready();
      } else {
        this._readyCallbacks.push(() => kalanfaModule.ready());
      }
    },

    /**
     * A method for directly registering language assets on the mediator.
     * This is used to set language assets as loaded and register them to the Vue intl
     * translation apparatus.
     * @param {string} moduleName - Module whose embedded translation template should be parsed
     * and registered
     */
    registerLanguageAssets(moduleName) {
      const messageElement = document.querySelector(`template[data-i18n="${moduleName}"]`);
      if (!messageElement) {
        return;
      }
      let messageMap;
      try {
        messageMap = JSON.parse(decodeMarkedSafeText(messageElement.innerHTML.trim()));
      } catch (e) {
        logger.error(`Error parsing language assets for ${moduleName}`);
      }
      if (!messageMap || typeof messageMap !== 'object') {
        logger.error(`Error parsing language assets for ${moduleName}`);
        return;
      }
      if (!Vue.registerMessages) {
        // Set this messageMap so that we can register it later when VueIntl
        // has finished loading.
        // Create empty entry in the language asset registry for this module if needed
        this._languageAssetRegistry[moduleName] = messageMap;
      } else {
        Vue.registerMessages(currentLanguage, messageMap);
      }
    },
    /**
     * A method for taking all registered language assets and registering them against Vue Intl.
     */
    registerMessages() {
      for (const moduleName in this._languageAssetRegistry) {
        Vue.registerMessages(currentLanguage, this._languageAssetRegistry[moduleName]);
      }
      delete this._languageAssetRegistry;
    },
    /**
     * A method for registering content viewers for asynchronous loading and track
     * which file types we have registered viewers for.
     * @param {string} kalanfaModuleName - Identifier of the module that provides the viewer
     * @param {string[]} kalanfaModuleUrls - the URLs of the Javascript
     * files that constitute the kalanfaModule
     * @param {string[]} contentPresets - the names of presets this content viewer can render
     */
    registerContentViewer(kalanfaModuleName, kalanfaModuleUrls, contentPresets) {
      this._contentViewerUrls[kalanfaModuleName] = kalanfaModuleUrls;
      contentPresets.forEach(preset => {
        if (this._contentViewerRegistry[preset]) {
          logger.warn(`Kalanfa Modules: Two content viewers are registering for ${preset}`);
        } else {
          this._contentViewerRegistry[preset] = kalanfaModuleName;
          Vue.component(preset + VIEWER_SUFFIX, () => ({
            /* Check the Kalanfa core app for a content viewer module that is able to
             * handle the rendering of the current content node.
             */
            component: this.retrieveContentViewer(preset),
            // A component to use while the async component is loading
            loading: ContentViewerLoading,
            // A component to use if the load fails
            error: ContentViewerError,
            // Delay before showing the loading component.
            delay: 0,
            // The error component will be displayed if a timeout is
            // provided and exceeded.
            timeout: 30000,
          }));
        }
      });
    },

    /**
     * A method for reading all templates that contain metadata about content viewers
     * and registering them.
     */
    registerAllContentViewers() {
      const contentViewerElements = Array.from(
        document.querySelectorAll('template[data-viewer]') || [],
      );
      for (const element of contentViewerElements) {
        const moduleName = element.getAttribute('data-viewer');
        try {
          const data = JSON.parse(decodeMarkedSafeText(element.innerHTML.trim()));
          const presets = data.presets;
          const urls = data.urls;
          this.registerContentViewer(moduleName, urls, presets);
        } catch (e) {
          logger.error(`Error parsing content viewer for ${moduleName}`);
        }
      }
    },

    /**
     * A method to retrieve a content viewer component.
     * @param {string} preset - Content preset whose viewer component should be resolved
     * @returns {Promise} Promise that resolves with loaded content viewer Vue component
     */
    retrieveContentViewer(preset) {
      return new Promise((resolve, reject) => {
        const kalanfaModuleName = this._contentViewerRegistry[preset];
        function resolveComponent(module) {
          if (module.viewerComponent) {
            resolve(module.viewerComponent);
          } else {
            reject(
              `Content viewer registered for ${preset} but no viewerComponent found in module ${kalanfaModuleName}`,
            );
          }
        }
        if (!kalanfaModuleName) {
          // Our content viewer registry does not have a viewer for this content preset.
          reject(`No registered content viewer available for preset: ${preset}`);
        } else if (this._kalanfaModuleRegistry[kalanfaModuleName]) {
          // There is a named viewer for this preset, and it is already loaded.
          resolveComponent(this._kalanfaModuleRegistry[kalanfaModuleName]);
        } else {
          // We have a content viewer for this, but it has not been loaded, so load it, and then
          // resolve the promise when it has been loaded.
          const allUrls = this._contentViewerUrls[kalanfaModuleName];
          const cssUrls = allUrls.filter(url => url.endsWith('css'));
          const jsUrls = allUrls.filter(url => !url.endsWith('css'));
          // Register CSS URLs with rtlManager so it can create tagged link elements
          // and switch direction later via the same loadDirectionalCSS code path.
          rtlManager.registerBundleCSS(kalanfaModuleName, cssUrls);
          rtlManager.loadRegisteredBundleCSS(kalanfaModuleName);
          Promise.all(jsUrls.map(scriptLoader))
            .then(() => {
              if (this._kalanfaModuleRegistry[kalanfaModuleName]) {
                resolveComponent(this._kalanfaModuleRegistry[kalanfaModuleName]);
              } else {
                // Wait until the module has been registered
                if (!this._contentViewerCallbacks[kalanfaModuleName]) {
                  this._contentViewerCallbacks[kalanfaModuleName] = [];
                }
                this._contentViewerCallbacks[kalanfaModuleName].push(module => {
                  resolveComponent(module);
                });
              }
            })
            .catch(error => {
              logger.error('Kalanfa Modules: ' + error);
              reject('Content viewer failed to load properly');
            });
        }
      });
    },
    /*
     * Method to load the direction specific CSS for a particular content viewer
     * @param {ContentViewerModule} contentViewerModule The content viewer module to load the
     * css for
     * @param {String} direction Must be one of languageDirections.RTL or LTR
     * @return {Promise} Promise that resolves when new CSS has loaded
     */
    loadDirectionalCSS(contentViewerModule, direction) {
      // Use the RTL manager to dynamically switch CSS direction for webpack bundles.
      // The RTL manager handles all CSS files for the bundle, not just a single file.
      const bundleName = contentViewerModule.name;

      if (direction === languageDirections.RTL) {
        return rtlManager.enableRTL(bundleName);
      } else if (direction === languageDirections.LTR) {
        return rtlManager.disableRTL(bundleName);
      } else {
        return Promise.reject(`Invalid direction: ${direction}`);
      }
    },
  };
  publicMethods.forEach(method => {
    facade[method] = mediator[method].bind(mediator);
  });
  return mediator;
}
