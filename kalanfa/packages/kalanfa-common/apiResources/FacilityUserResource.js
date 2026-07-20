import { Resource } from 'kalanfa/apiResource';
import urls from 'kalanfa/urls';
import client from 'kalanfa/client';

export default new Resource({
  name: 'facilityuser',
  removeImportedUser(user_id) {
    return client({
      url: urls['kalanfa:core:deleteimporteduser'](user_id),
      method: 'DELETE',
    });
  },
  async listRemoteFacilityLearners(params) {
    const { data } = await client({
      url: urls['kalanfa:core:remotefacilityauthenticateduserinfo'](),
      method: 'POST',
      data: params,
    });

    const admin = data.find(user => user.username === params.username);
    const students = data.filter(user => !user.roles || !user.roles.length);

    return {
      admin,
      students,
    };
  },
});
