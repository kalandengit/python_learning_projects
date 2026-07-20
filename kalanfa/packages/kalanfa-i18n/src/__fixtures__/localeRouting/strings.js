import { createTranslator } from 'kalanfa/utils/i18n';

const strings = createTranslator('RoutingTest', {
  hello: { message: 'Hello', context: 'A greeting' },
});

export default strings;
