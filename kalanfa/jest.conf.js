/* eslint-disable import-x/no-commonjs, import-x/no-amd, import-x/no-import-module-exports */
const baseConfig = require('kalanfa-jest-config/jest.conf');

module.exports = Object.assign(baseConfig, {
  // Only match *.spec.js files - exclude utility files in __tests__ folders
  testMatch: ['**/__tests__/**/*.spec.js', '**/?(*.)spec.js'],
  // Make sure we transpile any raw vue or ES6 files
  // Pattern handles both yarn flat structure and pnpm nested structure
  transformIgnorePatterns: [
    'node_modules/(?!(\\.pnpm/(keen-ui|epubjs|kalanfa-common|kalanfa|kalanfa-design-system|kalanfa-constants|uuid)|keen-ui|epubjs|kalanfa-common|kalanfa|kalanfa-design-system|kalanfa-constants|uuid))',
  ],
  collectCoverageFrom: [
    'kalanfa/**/frontend/**/*.{js,vue}',
    'packages/*/src/*.js',
    '!**/node_modules/**',
    '!**/__fixtures__/**',
  ],
});
