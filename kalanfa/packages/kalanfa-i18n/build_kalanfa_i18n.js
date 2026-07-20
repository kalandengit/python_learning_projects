/* Build file for kalanfa-i18n */
const fs = require('node:fs');
const path = require('node:path');

// Copy the kalanfa language_info.json into the kalanfa-i18n package for use externally

const languageInfo = require(path.resolve(__dirname, '../../kalanfa/locale/language_info.json'));

const outputPath = path.resolve(__dirname, './src/language_info.json');
fs.mkdirSync(path.dirname(outputPath), { recursive: true });

fs.writeFileSync(outputPath, JSON.stringify(languageInfo, undefined, 2), {
  encoding: 'utf-8',
});
