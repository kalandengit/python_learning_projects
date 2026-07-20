import { Resource } from 'kalanfa/apiResource';
import urls from 'kalanfa/urls';

export default new Resource({
  name: 'unitlessonprogress',
  namespace: 'kalanfa.plugins.coach',
  fetchProgress({ courseSessionId, unitContentnodeId }) {
    const url = urls['kalanfa:kalanfa.plugins.coach:unit_lesson_progress'](
      courseSessionId,
      unitContentnodeId,
    );
    return this.client({ url, method: 'GET' }).then(response => response.data);
  },
});
