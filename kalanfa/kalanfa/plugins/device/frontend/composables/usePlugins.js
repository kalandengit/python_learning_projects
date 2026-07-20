/**
 * A composable function containing logic related to channels
 */

import { ref } from 'vue';
import client from 'kalanfa/client';
import urls from 'kalanfa/urls';

export default function usePlugins() {
  const plugins = ref(null);
  const fetchPlugins = Promise.resolve(
    client({
      url: urls['kalanfa:core:plugins_list'](),
    }).then(response => {
      plugins.value = response.data;
    }),
  );

  function togglePlugin(pluginId, value) {
    const pluginIndex = plugins.value.findIndex(plugin => plugin.id === pluginId);
    if (pluginIndex !== -1) {
      const plugin = plugins.value[pluginIndex];
      if (plugin.enabled !== value) {
        return client({
          method: 'PATCH',
          url: urls['kalanfa:core:plugins_detail'](pluginId),
          data: {
            enabled: value,
          },
        }).then(response => {
          plugins.value.splice(pluginIndex, 1, response.data);
        });
      }
      return Promise.resolve();
    }
    return Promise.reject(new Error(`Plugin ${pluginId} not found`));
  }
  function enablePlugin(pluginId) {
    return togglePlugin(pluginId, true);
  }
  function disablePlugin(pluginId) {
    return togglePlugin(pluginId, false);
  }
  return {
    plugins,
    fetchPlugins,
    enablePlugin,
    disablePlugin,
    togglePlugin,
  };
}
