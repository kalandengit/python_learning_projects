import { ref } from 'vue';
import { set } from '@vueuse/core';
import client from 'kalanfa/client';
import urls from 'kalanfa/urls';
import plugin_data from 'kalanfa-plugin-data';

/** @typedef {import('vue').Ref} Ref */

/**
 * Whether the user is in any classes
 * @type {Ref<boolean>}
 */
export const inClasses = ref(false);
/**
 * Whether the user can download content externally from Kalanfa within the learn app
 * @type {Ref<boolean>}
 */
export const canDownloadExternally = ref(true);

/**
 * Whether learners can queue content downloads (to 'My Downloads')
 * @type {Ref<boolean>}
 */
export const canAddDownloads = ref(false);

export function prepareLearnApp() {
  set(canAddDownloads, plugin_data.allowLearnerDownloads);
  return client({ url: urls['kalanfa:kalanfa.plugins.learn:state']() }).then(response => {
    set(inClasses, response.data.in_classes);
    set(canDownloadExternally, response.data.can_download_externally);
  });
}

/**
 * Returns the learn-app's reactive state flags for classroom membership and download
 * permissions.
 * @returns {{
 *   canDownloadExternally: Ref<boolean>, canAddDownloads: Ref<boolean>, inClasses: Ref<boolean>
 * }} Reactive learn-app state.
 */
export default function useCoreLearn() {
  return {
    inClasses,
    canAddDownloads,
    canDownloadExternally,
  };
}
