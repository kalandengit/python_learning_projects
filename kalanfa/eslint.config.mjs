import kalanfaFormatConfig from 'kalanfa-format/eslint.config.mjs';

const CJS_RULES = {
  'import-x/no-commonjs': 'off',
  'import-x/no-amd': 'off',
  'import-x/no-import-module-exports': 'off',
};

export default [
  ...kalanfaFormatConfig,

  // Node.js-only packages — remain CommonJS until they migrate to ESM
  {
    files: [
      'packages/browserslist-config-kalanfa/**',
      'packages/eslint-plugin-kalanfa/**',
      'packages/kalanfa-build/**',
      'packages/kalanfa-format/**',
      'packages/kalanfa-glob/**',
      'packages/kalanfa-i18n/**',
      'packages/kalanfa-jest-config/**',
      'packages/kalanfa-logging/**',
      'packages/build_kalanfa_package.js',
    ],
    rules: CJS_RULES,
  },

  // Every plugin has a buildConfig.js — blanket exemption for all of them
  {
    files: ['**/buildConfig.js'],
    rules: CJS_RULES,
  },

  // Auto-generated static files — too numerous to annotate individually
  {
    files: ['kalanfa/**/static/**'],
    rules: CJS_RULES,
  },
];
