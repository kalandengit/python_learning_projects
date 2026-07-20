import { Resource } from 'kalanfa/apiResource';

export default new Resource({
  name: 'attendancerecord',
  bulkUpdate(data) {
    return this.postListEndpoint('bulk_update', data);
  },
});
