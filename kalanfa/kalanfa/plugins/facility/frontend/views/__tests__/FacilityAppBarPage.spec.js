import { render, screen } from '@testing-library/vue';
import '@testing-library/jest-dom';
import { ref } from 'vue';
import useKResponsiveWindow from 'kalanfa-design-system/lib/composables/useKResponsiveWindow';
import useFacilities, { useFacilitiesMock } from 'kalanfa-common/composables/useFacilities'; // eslint-disable-line
import useFacility, { useFacilityMock } from 'kalanfa-common/composables/useFacility'; // eslint-disable-line
import { coreStrings } from 'kalanfa/uiText/commonCoreStrings';
import FacilityAppBarPage from '../FacilityAppBarPage';

const { facilityLabel$ } = coreStrings;

const APP_BAR_TITLE = 'Facility settings';
const FACILITY_NAME = 'Sunrise School';

jest.mock('kalanfa/urls');
jest.mock('kalanfa-design-system/lib/composables/useKResponsiveWindow');
jest.mock('kalanfa-common/composables/useFacilities');
jest.mock('kalanfa-common/composables/useFacility');
jest.mock('kalanfa/components/pages/AppBarPage', () => ({
  name: 'AppBarPage',
  props: {
    title: {
      type: String,
      required: true,
    },
  },
  render(h) {
    return h('div', [
      h('h1', this.title),
      this.$scopedSlots.default ? this.$scopedSlots.default({ pageContentHeight: 600 }) : null,
    ]);
  },
}));

function renderPage(props = {}) {
  return render(FacilityAppBarPage, { props });
}

describe('FacilityAppBarPage', function () {
  beforeEach(() => {
    useKResponsiveWindow.mockImplementation(() => ({
      windowIsSmall: false,
    }));
  });

  it('shows the page title passed by the parent page', () => {
    useFacilities.mockReturnValue(useFacilitiesMock({ userIsMultiFacilityAdmin: ref(false) }));
    useFacility.mockReturnValue(useFacilityMock({ currentFacilityName: ref('') }));
    renderPage({ appBarTitle: APP_BAR_TITLE });
    expect(screen.getByRole('heading', { name: APP_BAR_TITLE })).toBeInTheDocument();
  });

  it('shows the current facility name for multi-facility admins', () => {
    useFacilities.mockReturnValue(useFacilitiesMock({ userIsMultiFacilityAdmin: ref(true) }));
    useFacility.mockReturnValue(useFacilityMock({ currentFacilityName: ref(FACILITY_NAME) }));
    renderPage();

    const expectedHeading = `${facilityLabel$()} – ${FACILITY_NAME}`;
    expect(screen.getByRole('heading', { name: expectedHeading })).toBeInTheDocument();
  });

  it('shows the default facility title for single-facility admins', () => {
    useFacilities.mockReturnValue(useFacilitiesMock({ userIsMultiFacilityAdmin: ref(false) }));
    useFacility.mockReturnValue(useFacilityMock({ currentFacilityName: ref('') }));
    renderPage();

    expect(screen.getByRole('heading', { name: facilityLabel$() })).toBeInTheDocument();
  });
});
