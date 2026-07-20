import { createTranslator } from 'kalanfa/utils/i18n';

export default createTranslator('ChannelUpdateStrings', {
  notAvailableFromDrives: {
    message: 'This channel was not found on any attached drives',
    context: "Error message that displays if channel can't be found on an external disk drive.",
  },
  notAvailableFromNetwork: {
    message: 'This channel was not found on any Kalanfa server on your network',
    context:
      "Error message that displays if a channel can't be found on the Kalanfa network. This may display when the user imports resources from a different device running Kalanfa in their same local network, or from a Kalanfa server hosted outside their LAN.\n\nKalanfa will try to automatically detect other instances (peers) running in the same LAN. If detection is unsuccessful, this message displays.",
  },
  notAvailableFromStudio: {
    message: 'This channel was not found on Kalanfa Studio',
    context: "Error message that displays if channel can't be found on Kalanfa Studio.",
  },
});
