import { get } from '@vueuse/core';
import { ref, onMounted } from 'vue';
import useUser from 'kalanfa/composables/useUser';
import client from 'kalanfa/client';
import urls from 'kalanfa/urls';

export default function onMyOwnSetup() {
  const onMyOwnSetup = ref(false);
  const { isLearnerOnlyImport } = useUser();

  onMounted(() => {
    client({ url: urls['kalanfa:kalanfa.plugins.user_profile:onmyownsetup']() }).then(response => {
      onMyOwnSetup.value = response.data.on_my_own_setup && !get(isLearnerOnlyImport);
    });
  });

  return {
    onMyOwnSetup,
  };
}
