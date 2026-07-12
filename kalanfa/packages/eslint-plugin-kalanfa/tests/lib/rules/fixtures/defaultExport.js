// Test fixture with default export
import { createTranslator } from 'kalanfa/utils/i18n';

export default createTranslator('DefaultExportNamespace', {
  defaultMessage: 'This is a default export',
  anotherMessage: 'Another message',
});
