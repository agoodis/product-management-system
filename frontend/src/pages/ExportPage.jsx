import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Grid,
  Card,
  CardContent,
  CardActions,
  Alert,
  CircularProgress
} from '@mui/material';
import { exportsApi } from '../services/api';
import DownloadIcon from '@mui/icons-material/Download';

const ExportCard = ({ title, description, onExport, loading }) => {
  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          {title}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {description}
        </Typography>
      </CardContent>
      <CardActions>
        <Button
          fullWidth
          variant="contained"
          startIcon={loading ? <CircularProgress size={20} /> : <DownloadIcon />}
          onClick={onExport}
          disabled={loading}
        >
          {loading ? 'Экспорт...' : 'Экспортировать'}
        </Button>
      </CardActions>
    </Card>
  );
};

const ExportPage = () => {
  const [loading, setLoading] = useState({});
  const [message, setMessage] = useState(null);

  const downloadFile = (blob, filename) => {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  };

  const handleExport = async (type) => {
    setLoading(prev => ({ ...prev, [type]: true }));
    setMessage(null);

    try {
      let response;
      let filename;

      switch (type) {
        case 'wb':
          response = await exportsApi.exportToWB();
          filename = `export_wb_${new Date().toISOString().split('T')[0]}.xlsx`;
          break;
        case 'ozon':
          response = await exportsApi.exportToOzon();
          filename = `export_ozon_${new Date().toISOString().split('T')[0]}.xlsx`;
          break;
        case 'full':
          response = await exportsApi.exportFull();
          filename = `export_full_${new Date().toISOString().split('T')[0]}.xlsx`;
          break;
        default:
          break;
      }

      downloadFile(response.data, filename);
      setMessage({
        type: 'success',
        text: `Файл ${filename} успешно экспортирован!`
      });
    } catch (err) {
      setMessage({
        type: 'error',
        text: `Ошибка экспорта: ${err.response?.data?.detail || err.message}`
      });
    } finally {
      setLoading(prev => ({ ...prev, [type]: false }));
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Экспорт данных
      </Typography>

      <Typography variant="body1" color="text.secondary" paragraph>
        Экспортируйте данные в формате Excel для загрузки на маркетплейсы или для анализа
      </Typography>

      {message && (
        <Alert 
          severity={message.type} 
          sx={{ mb: 3 }}
          onClose={() => setMessage(null)}
        >
          {message.text}
        </Alert>
      )}

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <ExportCard
            title="Экспорт для Wildberries"
            description="Выгрузка товаров с остатками и ценами для загрузки на WB"
            onExport={() => handleExport('wb')}
            loading={loading['wb']}
          />
        </Grid>

        <Grid item xs={12} md={4}>
          <ExportCard
            title="Экспорт для Ozon"
            description="Выгрузка товаров с остатками и ценами для загрузки на Ozon"
            onExport={() => handleExport('ozon')}
            loading={loading['ozon']}
          />
        </Grid>

        <Grid item xs={12} md={4}>
          <ExportCard
            title="Полная выгрузка"
            description="Полная выгрузка всех данных из базы, включая расчетные поля"
            onExport={() => handleExport('full')}
            loading={loading['full']}
          />
        </Grid>
      </Grid>

      <Paper sx={{ mt: 4, p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Информация об экспорте
        </Typography>
        <Typography variant="body2" paragraph>
          <strong>Wildberries:</strong> Включает штрихкод, артикул, название, бренд, размер, остаток, цену и скидку
        </Typography>
        <Typography variant="body2" paragraph>
          <strong>Ozon:</strong> Включает SKU, Ozon Product ID, все ценовые поля и минимальную цену
        </Typography>
        <Typography variant="body2">
          <strong>Полная выгрузка:</strong> Все данные из базы, включая информацию по всем маркетплейсам и расчетные показатели (наценка, оборачиваемость и т.д.)
        </Typography>
      </Paper>
    </Box>
  );
};

export default ExportPage;