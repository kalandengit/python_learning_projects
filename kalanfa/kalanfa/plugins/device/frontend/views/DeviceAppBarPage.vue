<template>

  <AppBarPage
    :title="title"
    :loading="loading"
  >
    <ImpactStoryBanner />
    <DeprecationWarningBanner style="margin-bottom: 1em" />

    <div>
      <slot></slot>
    </div>
  </AppBarPage>

</template>


<script>

  import AppBarPage from 'kalanfa/components/pages/AppBarPage';
  import ImpactStoryBanner from 'kalanfa-common/components/ImpactStoryBanner';
  import DeprecationWarningBanner from './DeprecationWarningBanner';

  export default {
    name: 'DeviceAppBarPage',
    components: { AppBarPage, ImpactStoryBanner, DeprecationWarningBanner },
    props: {
      title: {
        type: String,
        required: true,
      },
      loading: {
        type: Boolean,
        default: false,
      },
    },
  };

</script>
