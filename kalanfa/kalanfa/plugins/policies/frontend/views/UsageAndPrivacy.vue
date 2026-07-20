<template>

  <ImmersivePage
    :title="coreString('usageAndPrivacyLabel')"
    @cancel="$emit('cancel')"
  >
    <section v-if="!hideUsersSection">
      <h2>{{ coreString('usersLabel') }}</h2>
      <p>{{ $tr('kalanfaUsersP1') }}</p>
      <p>{{ $tr('kalanfaUsersP2') }}</p>
      <p>{{ $tr('kalanfaUsersP3') }}</p>
      <p>{{ $tr('kalanfaUsersP4') }}</p>
      <ul>
        <li>{{ $tr('kalanfaUsersL1') }}</li>
        <li>{{ $tr('kalanfaUsersL2') }}</li>
        <li>{{ $tr('kalanfaUsersL3') }}</li>
        <li>{{ $tr('kalanfaUsersL4') }}</li>
      </ul>
      <p>{{ $tr('kalanfaUsersP5') }}</p>
      <p>{{ $tr('kalanfaUsersP6') }}</p>
      <template v-if="oidcProviderEnabled">
        <h3>{{ $tr('openIdH1') }}</h3>
        <p>{{ $tr('openIdP1') }}</p>
      </template>
    </section>
    <section v-if="!hideOwnersSection">
      <h2>{{ $tr('kalanfaOwnersTitle') }}</h2>
      <p>{{ $tr('kalanfaOwnersP1') }}</p>
      <p>{{ $tr('kalanfaOwnersP2') }}</p>
      <p>{{ $tr('kalanfaOwnersP3') }}</p>
      <p>{{ $tr('kalanfaOwnersP4') }}</p>
    </section>
    <section v-if="!hideAboutSection">
      <h2>{{ $tr('kalanfaAboutTitle') }}</h2>
      <p>{{ $tr('kalanfaAboutP1') }}</p>
      <p>
        <!-- eslint-disable vue/no-bare-strings-in-template -->
        <KExternalLink
          text="https://learningequality.org"
          href="https://learningequality.org"
          :openInNewTab="true"
        />
        <!-- eslint-enable vue/no-bare-strings-in-template -->
      </p>
      <p>{{ $tr('kalanfaAboutP2') }}</p>
      <p>{{ $tr('kalanfaAboutP3') }}</p>
      <p>{{ $tr('kalanfaAboutP4') }}</p>
      <p>{{ $tr('kalanfaAboutP5') }}</p>
    </section>
    <template #actions>
      <!--
        Need to inject a button without type="submit" attribute
        so it doesn't force a submit event in the SetupWizard SuperuserCredentialsForm
      -->
      <KButton
        :text="coreString('closeAction')"
        primary
        @click="$emit('submit')"
      />
    </template>
  </ImmersivePage>

</template>


<script>

  import ImmersivePage from 'kalanfa/components/pages/ImmersivePage';
  import commonCoreStrings from 'kalanfa/uiText/commonCoreStrings';
  import plugin_data from 'kalanfa-plugin-data';

  export default {
    name: 'UsageAndPrivacy',
    components: { ImmersivePage },
    mixins: [commonCoreStrings],
    props: {
      hideUsersSection: {
        type: Boolean,
        default: false,
      },
      hideOwnersSection: {
        type: Boolean,
        default: false,
      },
      hideAboutSection: {
        type: Boolean,
        default: false,
      },
    },
    computed: {
      oidcProviderEnabled() {
        return plugin_data.oidcProviderEnabled;
      },
    },
    $trs: {
      kalanfaUsersP1: {
        message:
          'You should use Kalanfa in compliance with all applicable laws. This may mean obtaining permission from your parent, guardian, or teacher.',
        context:
          'This text forms part of the \'Usage and privacy\' information panel in Kalanfa. You can access the full text via the "Usage and privacy" link in the left navigation bar.',
      },
      kalanfaUsersP2: {
        message:
          'Be aware that your personal information may be visible to others, depending on how the software has been configured and how you access the software.',
        context:
          'This text forms part of the \'Usage and privacy\' information panel in Kalanfa. You can access the full text via the "Usage and privacy" link in the left navigation bar.',
      },
      kalanfaUsersP3: {
        message:
          "Please contact your local Kalanfa administrator to understand what personal information of yours might be stored, who it's visible to, how to update or delete it, or if you believe your account has been compromised.",
        context:
          'This text forms part of the \'Usage and privacy\' information panel in Kalanfa. You can access the full text via the "Usage and privacy" link in the left navigation bar.',
      },
      kalanfaUsersP4: {
        message: 'You should not:',
        context:
          'This text forms part of the \'Usage and privacy\' information panel in Kalanfa. You can access the full text via the "Usage and privacy" link in the left navigation bar.',
      },
      kalanfaUsersL1: {
        message:
          'Share your password, let anyone access your account, or do anything that might put your account at risk',
        context:
          'This text forms part of the \'Usage and privacy\' information panel in Kalanfa. You can access the full text via the "Usage and privacy" link in the left navigation bar.',
      },
      kalanfaUsersL2: {
        message: "Attempt to access any other user's account",
        context:
          'This text forms part of the \'Usage and privacy\' information panel in Kalanfa. You can access the full text via the "Usage and privacy" link in the left navigation bar.',
      },
      kalanfaUsersL3: {
        message:
          'Remove, circumvent, disable, damage or otherwise interfere with security-related features of Kalanfa',
        context:
          'This text forms part of the \'Usage and privacy\' information panel in Kalanfa. You can access the full text via the "Usage and privacy" link in the left navigation bar.',
      },
      kalanfaUsersL4: {
        message:
          "Intentionally interfere with or damage the operation of Kalanfa or any user's enjoyment of it, by any means",

        context: 'Part of the "Usage and privacy" recommendations.',
      },
      kalanfaUsersP5: {
        message:
          'When you use Kalanfa as a logged-in user, information such as your name, username, age, birth year, identification number, the resources that you view, and your performance on assessments may be made available to administrators and coaches in your facility. Your information may also be used by the developers of Kalanfa and shared with content creators to help improve the software and resources for different learner types and needs.',
        context:
          'This text forms part of the \'Usage and privacy\' information panel in Kalanfa. You can access the full text via the "Usage and privacy" link in the left navigation bar.',
      },
      kalanfaUsersP6: {
        message:
          'When you use Kalanfa as a guest, aggregate information about the resources you and other guest users view may be available to administrators and certain coaches.',
        context:
          'This text forms part of the \'Usage and privacy\' information panel in Kalanfa. You can access the full text via the "Usage and privacy" link in the left navigation bar.',
      },
      kalanfaOwnersTitle: {
        message: 'Administrators',
        context:
          'Title of a section in the \'Usage and privacy\' information panel. The section contains information about for administrators who are running and maintaining Kalanfa.\n\nYou can access the full text via the "Usage and privacy" link in the left navigation bar.',
      },
      kalanfaOwnersP1: {
        message:
          'You should run Kalanfa as a service in compliance with all applicable laws. If you are the owner of the device that Kalanfa is installed on, please be aware that you are ultimately responsible for the safety and protection of the user data that gets stored in Kalanfa.',
        context:
          'This text forms part of the \'Usage and privacy\' information panel in Kalanfa. You can access the full text via the "Usage and privacy" link in the left navigation bar.',
      },
      kalanfaOwnersP2: {
        message:
          "You should also follow best information security practices for protecting your users' data. This includes keeping the device physically secure, encrypting the hard drive, using strong and unique passwords, keeping the operating system up-to-date, and having a properly-configured firewall.",
        context:
          'This text forms part of the \'Usage and privacy\' information panel in Kalanfa. You can access the full text via the "Usage and privacy" link in the left navigation bar.',
      },
      kalanfaOwnersP3: {
        message:
          'If you choose to sync your facility data to the Kalanfa Data Portal, you would be granting Kalanfa Data Portal organization administrators access to your data. You would also be granting access to Learning Equality, who operates the servers.',
        context:
          'This text forms part of the \'Usage and privacy\' information panel in Kalanfa. You can access the full text via the "Usage and privacy" link in the left navigation bar.',
      },
      kalanfaOwnersP4: {
        message:
          'Please ensure that your users have way of getting in touch with you if they have concerns about their accounts.',
        context:
          'This text forms part of the \'Usage and privacy\' information panel in Kalanfa. You can access the full text via the "Usage and privacy" link in the left navigation bar.',
      },
      kalanfaAboutTitle: {
        message: 'About Kalanfa',
        context:
          "Title of a section in the 'Usage and privacy' information panel. The section contains information about Kalanfa.\n\nYou can access the full text via the 'Usage and privacy' link in the left navigation bar.\n",
      },
      kalanfaAboutP1: {
        message:
          "The Kalanfa software is built by Foundation for Learning Equality, Inc. More information, including Kalanfa's Terms of Service and Privacy Policy, can be found at:",
        context:
          'This text forms part of the \'Usage and privacy\' information panel in Kalanfa. You can access the full text via the "Usage and privacy" link in the left navigation bar.',
      },
      kalanfaAboutP2: {
        message:
          'Kalanfa is a software application that can be installed on a wide variety of devices without needing a connection to the internet.',
        context:
          'This text forms part of the \'Usage and privacy\' information panel in Kalanfa. You can access the full text via the "Usage and privacy" link in the left navigation bar.',
      },
      kalanfaAboutP3: {
        message:
          'Unlike many online web services that are similarly accessed through a web browser, there are thousands of independent Kalanfa installations around the world – including this one. Each Kalanfa installation is managed and controlled by the owner of the device that it is installed on.',
        context:
          'This text forms part of the \'Usage and privacy\' information panel in Kalanfa. You can access the full text via the "Usage and privacy" link in the left navigation bar.',
      },
      kalanfaAboutP4: {
        message:
          'It is also possible for administrators to sync Kalanfa data to the cloud-based Kalanfa Data Portal service. If this occurs, all facility data will be accessible to organization admins on Kalanfa Data Portal. It will be uploaded to cloud servers operated by Learning Equality, who will also have access to this data.',
        context:
          'This text forms part of the \'Usage and privacy\' information panel in Kalanfa. You can access the full text via the "Usage and privacy" link in the left navigation bar.',
      },
      kalanfaAboutP5: {
        message:
          'In order to improve the quality of Kalanfa and the resources on it, Learning Equality collects anonymized usage information when Kalanfa has access to the internet. This includes IP addresses associated with the server, and device details such as the operating system and time zone. We also collect aggregate statistics including: number of users and facilities, birth year and gender distribution, and resource popularity. We make every effort to avoid collecting personally identifying information about Kalanfa users.',
        context:
          'This text forms part of the \'Usage and privacy\' information panel in Kalanfa. You can access the full text via the "Usage and privacy" link in the left navigation bar.',
      },
      openIdH1: {
        message: 'Signing in to third-party applications using Kalanfa',
        context:
          'This text forms part of the \'Usage and privacy\' information panel in Kalanfa. You can access the full text via the "Usage and privacy" link in the left navigation bar.',
      },
      openIdP1: {
        message:
          'It is possible to use Kalanfa to register or sign in to third-party applications. If you do this, the other application will have access to your Kalanfa username, unique user ID, and full name.',
        context:
          'This text forms part of the \'Usage and privacy\' information panel in Kalanfa. You can access the full text via the "Usage and privacy" link in the left navigation bar.',
      },
    },
  };

</script>
