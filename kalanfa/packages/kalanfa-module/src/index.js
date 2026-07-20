/**
 * KalanfaModule module.
 * Provides the base class for Kalanfa Modules - all Kalanfa Modules must extend this Base class.
 * @module kalanfaModule
 */

import coreApp from 'kalanfa';

export default class KalanfaModule {
  /**
   * An array of options to select from the options object passed into the constructor.
   * @type {string[]}
   */
  get kalanfaModuleOptions() {
    return [];
  }
  /**
   * The constructor function for the base KalanfaModule object.
   * @class
   * @param {object} options - An options hash to set properties of the object.
   * @param {Array} args - Any additional arguments that will be passed to initialize.
   */
  constructor(options, ...args) {
    /* eslint-disable no-undef */
    // __kalanfaModuleName is replaced during webpack compilation with the name derived from
    // the unique_slug that is defined on the class that defines the frontend kalanfaModule.
    this.name = __kalanfaModuleName;
    /* eslint-enable no-undef */
    const safeOptions = {};
    this.kalanfaModuleOptions.forEach(option => {
      if (options[option]) {
        safeOptions[option] = options[option];
      }
    });
    Object.assign(this, safeOptions);
    // Pass all arguments to the constructor directly to initialize for easy access.
    this.initialize(options, ...args);
    // Register the kalanfaModule with the Kalanfa core app.
    this._registerKalanfaModule();
  }

  /**
   * Method to automatically register the kalanfaModule with the Kalanfa core app once it has
   * initialized.
   * @private
   */
  _registerKalanfaModule() {
    coreApp.registerKalanfaModuleSync(this);
  }

  /**
   * A dummy initialization function - this function will be passed anything passed to the
   * constructor.
   * Useful for setting up the kalanfaModule before it is registered against the Kalanfa core app.
   */
  initialize() {}

  /**
   * A dummy ready function
   * Useful for initiating behaviour of the kalanfaModule after it is registered against the
   * Kalanfa core app.
   */
  ready() {}

  get Kalanfa() {
    return coreApp;
  }
}
