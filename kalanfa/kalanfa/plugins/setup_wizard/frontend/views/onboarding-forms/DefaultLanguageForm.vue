<template>

  <OnboardingStepBase
    :title="$tr('languageFormHeader')"
    @continue="handleSubmit"
  >
    <LanguageSwitcherList />
  </OnboardingStepBase>

</template>


<script>

  import LanguageSwitcherList from 'kalanfa/components/language-switcher/LanguageSwitcherList';
  import OnboardingStepBase from '../OnboardingStepBase';

  export default {
    name: 'DefaultLanguageForm',
    components: {
      OnboardingStepBase,
      LanguageSwitcherList,
    },
    inject: ['wizardService'],
    methods: {
      handleSubmit() {
        this.wizardService.send('CONTINUE');
      },
    },
    $trs: {
      languageFormHeader: {
        message: 'Please select the default language for Kalanfa',
        context: 'Admins must pick the default language they want to use in Kalanfa.',
      },
    },
  };

</script>


<style lang="scss" scoped></style>
