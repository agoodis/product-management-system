import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Container,
  Box,
  CssBaseline,
  ThemeProvider,
  createTheme
} from '@mui/material';
import ProductsTable from './components/ProductsTable';
import ImportPage from './pages/ImportPage';
import ExportPage from './pages/ExportPage';
import InventoryIcon from '@mui/icons-material/Inventory';
import UploadIcon from '@mui/icons-material/Upload';
import DownloadIcon from '@mui/icons-material/Download';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
          <AppBar position="static">
            <Toolbar>
              <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
                Система управления товарами
              </Typography>
              <Button
                color="inherit"
                component={Link}
                to="/"
                startIcon={<InventoryIcon />}
              >
                Товары
              </Button>
              <Button
                color="inherit"
                component={Link}
                to="/import"
                startIcon={<UploadIcon />}
              >
                Импорт
              </Button>
              <Button
                color="inherit"
                component={Link}
                to="/export"
                startIcon={<DownloadIcon />}
              >
                Экспорт
              </Button>
            </Toolbar>
          </AppBar>

          <Container maxWidth={false} sx={{ flexGrow: 1, py: 3, overflow: 'auto' }}>
            <Routes>
              <Route path="/" element={<ProductsTable />} />
              <Route path="/import" element={<ImportPage />} />
              <Route path="/export" element={<ExportPage />} />
            </Routes>
          </Container>
        </Box>
      </Router>
    </ThemeProvider>
  );
}

export default App;