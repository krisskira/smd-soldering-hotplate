import { createContext, useContext } from 'react';

export type ThemeName = 'light' | 'dark';

export const ThemeContext = createContext<{ theme: ThemeName; toggle: () => void }>({
  theme: 'light',
  toggle: () => {},
});

export function useTheme() {
  return useContext(ThemeContext);
}
