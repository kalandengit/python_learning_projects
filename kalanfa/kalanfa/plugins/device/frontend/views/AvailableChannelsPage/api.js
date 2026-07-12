import client from 'kalanfa/client';
import urls from 'kalanfa/urls';

export function getFreeSpaceOnServer() {
  return client({ url: urls['kalanfa:core:deviceinfo']() }).then(response => {
    return {
      freeSpace: response.data.content_storage_free_space,
    };
  });
}
