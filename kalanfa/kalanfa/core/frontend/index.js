/**
 * Provides the public API for the Kalanfa FrontEnd core app.
 * @module Facade
 */
// Import this first to ensure that we do a browser compatibility check before anything else
import './minimumBrowserRequirements';
import coreApp from 'kalanfa';
import logging from 'kalanfa-logging';
import store from 'kalanfa/store';
import heartbeat from 'kalanfa/heartbeat';
import { i18nSetup } from 'kalanfa/utils/i18n';
import coreModule from './state/modules/core';

// set up logging
logging.setDefaultLevel(process.env.NODE_ENV === 'production' ? 2 : 0);

// Register core module
store.registerModule('core', coreModule);

// Start the heartbeat polling here, as any URL needs should be set by now
heartbeat.startPolling();

i18nSetup().then(coreApp.ready);

// This is exported by webpack as the kalanfaCoreAppGlobal object, due to the 'output.library' flag
// which exports the coreApp at the bottom of this file as a named global variable:
// https://webpack.github.io/docs/configuration.html#output-library
export default coreApp;
