<template>

  <div class="container">
    <div class="rel">
      <div class="flapping-kalanfa">
        <KLogo
          size="250"
          :animate="true"
          :altText="$tr('kalanfaLoading')"
        />
      </div>
    </div>
  </div>

</template>


<script>

  export default {
    name: 'KalanfaLoadingSnippet',
    $trs: {
      kalanfaLoading: {
        message: 'Kalanfa loading',
        context: 'Indicates Kalanfa is loading',
      },
    },
  };

</script>


<style>

  .rel {
    position: relative;
    width: 100%;
    height: 100%;
  }

  .flapping-kalanfa {
    /* Set the width of this to match the size prop to center it */
    width: 250px;
    margin: 0 auto;
    animation: fadeIn;
    animation-duration: 1s;
    animation-delay: 1s;
    animation-fill-mode: both;
  }

</style>
