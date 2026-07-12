import client from 'kalanfa/client';
import urls from 'kalanfa/urls';

/**
 * Ask the server whether the current connection is metered.
 * @returns {Promise<boolean>} Resolves with the server-reported metered-connection state.
 */
export default function checkIsMetered() {
  const urlFunction = urls['kalanfa:core:check_metered_connection'];
  return client({ url: urlFunction() }).then(response => response.data);
}
