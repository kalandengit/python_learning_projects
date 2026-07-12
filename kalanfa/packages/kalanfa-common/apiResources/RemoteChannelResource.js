import { Resource } from 'kalanfa/apiResource';

export default new Resource({
  name: 'remotechannel',
  getKalanfaStudioStatus() {
    return this.getListEndpoint('kalanfa_studio_status');
  },
});
