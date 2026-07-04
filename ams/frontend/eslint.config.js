import js from '@eslint/js';
import tseslint from 'typescript-eslint';

export default tseslint.config(
  { ignores: ['dist'] },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: ['src/**/*.{ts,tsx}'],
    languageOptions: {
      globals: { crypto: 'readonly', window: 'readonly', document: 'readonly' },
    },
    rules: {
      // Section 11.4: raw MUI imports only via the wrapper layer once
      // components/ lands; rule seeded here so the convention is enforced early.
      'no-restricted-imports': ['warn', { patterns: [] }],
    },
  },
);
