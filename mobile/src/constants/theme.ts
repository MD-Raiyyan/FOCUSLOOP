import { Platform } from 'react-native';

/**
 * Luminous Clarity Design System Tokens
 * Derived directly from stitch_minimalist_mobile_app_ui/luminous_clarity/DESIGN.md
 */
export const Palette = {
  primary: '#493ee5',
  primaryContainer: '#635bff',
  onPrimary: '#ffffff',
  onPrimaryContainer: '#fefaff',
  primaryFixed: '#e2dfff',
  primaryFixedDim: '#c3c0ff',
  onPrimaryFixed: '#0f0069',
  onPrimaryFixedVariant: '#321ed2',

  secondary: '#006c49',
  onSecondary: '#ffffff',
  secondaryContainer: '#6cf8bb',
  onSecondaryContainer: '#00714d',
  secondaryFixed: '#6ffbbe',
  secondaryFixedDim: '#4edea3',
  onSecondaryFixed: '#002113',
  onSecondaryFixedVariant: '#005236',

  tertiary: '#815100',
  onTertiary: '#ffffff',
  tertiaryContainer: '#a36700',
  onTertiaryContainer: '#fffaf9',
  tertiaryFixed: '#ffddb8',
  tertiaryFixedDim: '#ffb95f',

  error: '#ba1a1a',
  onError: '#ffffff',
  errorContainer: '#ffdad6',

  background: '#fcf8ff',
  onBackground: '#1b1b24',
  surface: '#fcf8ff',
  onSurface: '#1b1b24',
  onSurfaceVariant: '#464555',
  surfaceDim: '#dcd8e6',
  surfaceBright: '#fcf8ff',
  surfaceContainerLowest: '#ffffff',
  surfaceContainerLow: '#f5f2ff',
  surfaceContainer: '#f0ecfa',
  surfaceContainerHigh: '#eae6f4',
  surfaceContainerHighest: '#e4e1ee',
  surfaceVariant: '#e4e1ee',

  // Categorical Pastel Washes
  surfaceTintViolet: '#F2F0FF',
  surfaceTintBlue: '#EDF5FF',
  surfaceTintRose: '#FFF0F0',
  surfaceTintMint: '#ECFDF5',
  surfaceTintAmber: '#FFFBEB',

  // Accents & Neutrals
  accentSky: '#38BDF8',
  accentIndigo: '#4F46E5',
  accentCoral: '#F43F5E',
  neutralCanvas: '#F8FAFC',
  neutralCard: '#FFFFFF',
  neutralBorder: '#EEF2F6',

  textStrong: '#111827',
  textSubtle: '#64748B',
  textMuted: '#94A3B8',

  outline: '#777587',
  outlineVariant: '#c7c4d8',
} as const;

export const Colors = {
  ...Palette,
  light: {
    text: '#111827',
    background: '#fcf8ff',
    backgroundElement: '#F0ECFA',
    backgroundSelected: '#F2F0FF',
    textSecondary: '#64748B',
  },
  dark: {
    text: '#ffffff',
    background: '#1b1b24',
    backgroundElement: '#302f39',
    backgroundSelected: '#464555',
    textSecondary: '#c7c4d8',
  },
} as const;

export type ThemeColor = keyof typeof Colors.light & keyof typeof Colors.dark;

export const Fonts = Platform.select({
  ios: {
    sans: 'System',
    serif: 'Serif',
    rounded: 'System',
    mono: 'Courier',
  },
  default: {
    sans: 'sans-serif',
    serif: 'serif',
    rounded: 'sans-serif-rounded',
    mono: 'monospace',
  },
  web: {
    sans: "'Plus Jakarta Sans', sans-serif",
    serif: 'serif',
    rounded: "'Plus Jakarta Sans', sans-serif",
    mono: 'monospace',
  },
});

export const Spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 20,
  xl: 28,
  gutterSm: 12,
  marginSm: 16,
  gutter: 16,
  margin: 24,
  // Backward compatibility
  half: 2,
  one: 4,
  two: 8,
  three: 16,
  four: 24,
  five: 32,
  six: 64,
} as const;

export const BorderRadius = {
  sm: 8,
  DEFAULT: 16,
  lg: 20,
  xl: 24,
  full: 9999,
} as const;

export const BottomTabInset = Platform.select({ ios: 50, android: 80 }) ?? 0;
export const MaxContentWidth = 800;
