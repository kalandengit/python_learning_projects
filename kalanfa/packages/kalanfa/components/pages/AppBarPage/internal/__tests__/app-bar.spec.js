import { shallowMount } from '@vue/test-utils';
import useKResponsiveWindow from 'kalanfa-design-system/lib/composables/useKResponsiveWindow';
import AppBar from '../AppBar';

jest.mock('kalanfa/urls');
jest.mock('kalanfa-design-system/lib/composables/useKResponsiveWindow');
jest.mock('kalanfa/composables/useUser');
jest.mock('vue-router/composables', () => ({
  useRoute: jest.fn(() => ({ params: {}, query: {} })),
}));

function createWrapper({ propsData } = {}) {
  const node = document.createElement('div');
  document.body.appendChild(node);
  return shallowMount(AppBar, {
    propsData,
    attachTo: node,
  });
}

describe('app bar component', () => {
  beforeAll(() => {
    useKResponsiveWindow.mockImplementation(() => ({}));
  });
  describe('smoke test', () => {
    it('should render', () => {
      const wrapper = createWrapper({ loading: false });
      expect(wrapper.findComponent(AppBar).element).toBeVisible();
    });
  });
});
