import client from 'kalanfa/client';
import urls from 'kalanfa/urls';

const url = urls['kalanfa:core:facility_create_facility']();

export function createFacility(payload) {
  return client({
    url,
    method: 'POST',
    data: payload,
  });
}
