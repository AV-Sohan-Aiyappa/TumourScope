import React from 'react';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import TumorDetector from './frontend/src/components/TumorDetector';
import theme from './frontend/src/theme';

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <TumorDetector />
    </ThemeProvider>
  );
}

export default App;
import theme from './frontend/src/theme'; // Import the theme from the correct path