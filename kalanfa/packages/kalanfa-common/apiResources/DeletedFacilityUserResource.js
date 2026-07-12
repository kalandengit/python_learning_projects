import { Resource } from 'kalanfa/apiResource';
import client from 'kalanfa/client';

export default new Resource({
  name: 'deletedfacilityuser',
  restoreCollection(getParams) {
    if (!getParams) {
      throw new Error('You must provide a getParams object to restore deleted users.');
    }
    return client({
      url: this.getUrlFunction('restore')(),
      method: 'POST',
      params: getParams,
    });
  },
});
