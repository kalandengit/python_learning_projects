import { Resource } from 'kalanfa/apiResource';

export default new Resource({
  name: 'attendancesession',
  fetchRecentSessions(getParams) {
    return this.fetchListCollection('recent', getParams);
  },
});
