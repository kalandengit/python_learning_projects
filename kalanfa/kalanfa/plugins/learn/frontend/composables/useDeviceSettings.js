import { computed, ref } from 'vue';
import store from 'kalanfa/store';
import plugin_data from 'kalanfa-plugin-data';

const allowDownloadOnMeteredConnection = ref(plugin_data.allowDownloadOnMeteredConnection);

export default function useDeviceSettings() {
  const allowGuestAccess = computed(() => store.getters.allowGuestAccess);
  const canAccessUnassignedContent = computed(() => store.getters.canAccessUnassignedContent);

  return {
    allowGuestAccess,
    canAccessUnassignedContent,
    allowDownloadOnMeteredConnection,
  };
}
