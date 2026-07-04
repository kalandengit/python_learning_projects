import { createTheme } from '@mui/material/styles';

/**
 * MUI v7 theme — Section 11.4 design tokens.
 * CSS variables enable light/dark without re-render; semantic severity
 * colors are contrast-checked (>= 4.5:1) in both schemes (WCAG 2.2 AA).
 */
export const theme = createTheme({
  cssVariables: true,
  colorSchemes: {
    light: {
      palette: {
        primary: { main: '#1a5fb4' },
        success: { main: '#1b7f37' }, // severity.permit
        error: { main: '#c01c28' },   // severity.deny
        warning: { main: '#b3550c' }, // severity.alarm
      },
    },
    dark: {
      palette: {
        primary: { main: '#62a0ea' },
        success: { main: '#57e389' },
        error: { main: '#ff7b63' },
        warning: { main: '#ffbe6f' },
      },
    },
  },
  shape: { borderRadius: 8 },
  spacing: 4,
  typography: {
    fontFamily: 'Inter, system-ui, sans-serif',
    fontSize: 14,
    body1: { lineHeight: 1.5 },
  },
  components: {
    MuiButtonBase: {
      defaultProps: { disableRipple: false },
    },
    MuiChip: {
      // Status is never colour-only (WCAG 1.4.1): StateChip wrapper adds icon + label.
      defaultProps: { variant: 'outlined' },
    },
  },
});
