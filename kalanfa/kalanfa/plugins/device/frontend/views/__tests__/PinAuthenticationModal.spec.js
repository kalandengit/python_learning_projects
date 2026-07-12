import { render, screen, fireEvent, waitFor } from '@testing-library/vue';
import userEvent from '@testing-library/user-event';
import client from 'kalanfa/client';
import urls from 'kalanfa/urls';
import { coreStrings } from 'kalanfa/uiText/commonCoreStrings';
import PinAuthenticationModal, { strings as pinModalStrings } from '../PinAuthenticationModal';

const { cancelAction$, continueAction$, requiredFieldError$, numbersOnly$ } = coreStrings;
const { incorrectPin$, pinPlaceholder$ } = pinModalStrings;

jest.mock('kalanfa/client');
jest.mock('kalanfa/urls');

const renderComponent = (options = {}) => {
  return render(PinAuthenticationModal, {
    props: {
      facilityDatasetId: 'test-facility-id',
    },
    ...options,
  });
};

describe('PinAuthenticationModal', () => {
  beforeEach(() => {
    client.mockResolvedValue({ data: { is_pin_valid: true } });
    urls['kalanfa:core:ispinvalid'] = jest.fn().mockReturnValue('/api/mock/ispinvalid/');
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('emits cancel when the user clicks Cancel', async () => {
    const { emitted } = renderComponent();

    await fireEvent.click(screen.getByRole('button', { name: cancelAction$() }));

    expect(emitted()).toHaveProperty('cancel');
    expect(emitted().cancel).toHaveLength(1);
  });

  describe('submitting a PIN', () => {
    it('does not show validation messages before the user submits the form', () => {
      renderComponent();

      expect(screen.queryByText(incorrectPin$())).not.toBeInTheDocument();
      expect(screen.queryByText(requiredFieldError$())).not.toBeInTheDocument();
      expect(screen.queryByText(numbersOnly$())).not.toBeInTheDocument();
    });

    it('emits submit when the user enters a valid PIN and submits', async () => {
      const { emitted } = renderComponent();

      await userEvent.type(screen.getByLabelText(pinPlaceholder$()), '1234');
      await fireEvent.click(screen.getByRole('button', { name: continueAction$() }));

      await waitFor(() => {
        expect(emitted()).toHaveProperty('submit');
      });

      expect(client).toHaveBeenCalledWith(
        expect.objectContaining({
          method: 'POST',
          data: { pin_code: '1234' },
        }),
      );
    });

    it('shows an incorrect PIN message when the submitted PIN is invalid', async () => {
      client.mockResolvedValue({ data: { is_pin_valid: false } });

      renderComponent();

      await userEvent.type(screen.getByLabelText(pinPlaceholder$()), '1234');
      await fireEvent.click(screen.getByRole('button', { name: continueAction$() }));

      await waitFor(() => {
        expect(screen.getByText(incorrectPin$())).toBeInTheDocument();
      });
    });

    it('shows a numbers-only validation message when the PIN contains letters', async () => {
      renderComponent();

      await userEvent.type(screen.getByLabelText(pinPlaceholder$()), 'abcd');
      await fireEvent.click(screen.getByRole('button', { name: continueAction$() }));

      expect(screen.getByText(numbersOnly$())).toBeInTheDocument();
    });

    it('shows a required-field validation message when the PIN is empty', async () => {
      renderComponent();

      await fireEvent.click(screen.getByRole('button', { name: continueAction$() }));

      expect(screen.getByText(requiredFieldError$())).toBeInTheDocument();
    });
  });
});
