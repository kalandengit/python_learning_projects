import './main.scss'; // attaches styles globally
import { setBrandColors, setTokenMapping } from 'kalanfa-design-system/lib/styles/theme';
import generateGlobalStyles from 'kalanfa-design-system/lib/styles/generateGlobalStyles';
import { set } from 'vue';
import trackInputModality from 'kalanfa-design-system/lib/styles/trackInputModality';
import trackMediaType from 'kalanfa-design-system/lib/styles/trackMediaType';
import themeConfig from 'kalanfa/styles/themeConfig';
import { validateObject, objectWithDefaults } from 'kalanfa/utils/objectSpecs';
import plugin_data from 'kalanfa-plugin-data';
import themeSpec from './themeSpec';

export function setThemeConfig(theme) {
  Object.keys(themeConfig).forEach(key => {
    set(themeConfig, key, theme[key]);
  });
}

export default function initializeTheme() {
  validateObject(plugin_data.kalanfaTheme, themeSpec);
  const theme = objectWithDefaults(plugin_data.kalanfaTheme, themeSpec);
  if (theme.brandColors) {
    setBrandColors(theme.brandColors);
  }
  setTokenMapping(theme.tokenMapping);
  setThemeConfig(theme);
  generateGlobalStyles();
  trackInputModality();
  trackMediaType();
}
