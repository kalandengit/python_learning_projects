import { Resource } from 'kalanfa/apiResource';
import urls from 'kalanfa/urls';

export default new Resource({
  name: 'unitreport',
  namespace: 'kalanfa.plugins.coach',
  fetchReport({ courseSessionId, unitContentnodeId }) {
    const url = urls['kalanfa:kalanfa.plugins.coach:unitreport'](
      courseSessionId,
      unitContentnodeId,
    );
    return this.client({ url, method: 'GET' }).then(response => response.data);
  },
});
