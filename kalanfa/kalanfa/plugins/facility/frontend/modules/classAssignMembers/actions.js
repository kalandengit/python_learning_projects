import MembershipResource from 'kalanfa-common/apiResources/MembershipResource';
import RoleResource from 'kalanfa-common/apiResources/RoleResource';
import { UserKinds } from 'kalanfa/constants';
import uniq from 'lodash/uniq';

export function enrollLearnersInClass(store, { classId, users }) {
  return MembershipResource.saveCollection({
    getParams: {
      collection: classId,
    },
    data: uniq(users).map(userId => ({
      collection: classId,
      user: userId,
    })),
  });
}

export function assignCoachesToClass(store, { classId, coaches }) {
  return RoleResource.saveCollection({
    getParams: {
      collection: classId,
    },
    data: uniq(coaches).map(userId => ({
      collection: classId,
      user: userId,
      kind: UserKinds.COACH,
    })),
  });
}
