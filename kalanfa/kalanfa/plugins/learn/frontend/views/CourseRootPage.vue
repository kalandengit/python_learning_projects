<template>

  <router-view />

</template>


<script>

  import usePreviousRoute from 'kalanfa-common/composables/usePreviousRoute';

  export default {
    name: 'CourseRootPage',
    setup() {
      usePreviousRoute();
    },
  };

</script>
