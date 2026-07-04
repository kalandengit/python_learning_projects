import { Routes, Route, Link as RouterLink } from 'react-router';
import {
  AppBar, Box, Container, Link, Toolbar, Typography,
} from '@mui/material';
import VisitsPage from './pages/VisitsPage';

/**
 * Shell per Section 11.1: skip-link first (WCAG keyboard), landmark
 * structure, left-rail navigation collapses on small screens (full nav
 * model lands with the remaining route bundles).
 */
export default function App() {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <Link
        href="#main"
        sx={{
          position: 'absolute',
          left: -9999,
          '&:focus': { left: 8, top: 8, zIndex: 1300, bgcolor: 'background.paper', p: 2 },
        }}
      >
        Skip to main content
      </Link>
      <AppBar position="static" component="header">
        <Toolbar>
          <Typography variant="h6" component="span" sx={{ flexGrow: 1 }}>
            AMS — Access Management
          </Typography>
          <nav aria-label="Primary">
            <Link component={RouterLink} to="/visits" color="inherit" underline="hover">
              Visits
            </Link>
          </nav>
        </Toolbar>
      </AppBar>
      <Container component="main" id="main" sx={{ py: 6, flexGrow: 1 }}>
        <Routes>
          <Route path="/" element={<VisitsPage />} />
          <Route path="/visits" element={<VisitsPage />} />
        </Routes>
      </Container>
    </Box>
  );
}
