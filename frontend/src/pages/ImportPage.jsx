import React, { useState, useEffect } from 'react';
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
  CircularProgress,
  List,
  ListItem,
  ListItemText,
  Chip
} from '@mui/material';
import { importsApi } from '../services/api';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';

const ImportCard = ({ title, description, onUpload, loading }) => {
  const [selectedFile, setSelectedFile] = useState(null);

  const handleFileChange = (event) => {
    setSelectedFile(event.target.files[0]);
  };

  const handleUpload = async () => {
    if (selectedFile) {
      await onUpload(selectedFile);
      setSelectedFile(null);
    }
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          {title}
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          {description}
        </Typography>
        <input
          type="file"
          accept=".xlsx,.xls"
          onChange={handleFileChange}
          style={{ display: 'none' }}
          id={`file-input-${title}`}
        />
        <label htmlFor={`file-input-${title}`}>
          <Button
            variant="outlined"
            component="span"
            startIcon={<CloudUploadIcon />}
            fullWidth
          >
            Выбрать файл
          </Button>
        </label>
        {selectedFile && (
          <Typography variant="body2" sx={{ mt: 1 }}>
            Выбран: {selectedFile.name}
          </Typography>
        )}
      </CardContent>
      <CardActions>
        <Button
          fullWidth
          variant="contained"
          onClick={handleUpload}
          disabled={!selectedFile || loading}
        >
          {loading ? <CircularProgress size={24} /> : 'Загрузить'}
        </Button>
      </CardActions>
    </Card>
  );
};

const ImportPage = () => {
  const [loading, setLoading] = useState({});
  const [message, setMessage] = useState(null);
  const [logs, setLogs] = useState([]);

  const loadLogs = async () => {
    try {
      const response = await importsApi.getLogs(20);
      setLogs(response.data);
    } catch (err) {
      console.error('Ошибка загрузки логов:', err);
    }
  };

  useEffect(() => {
    loadLogs();
  }, []);

  const handleImport = async (type, file) => {
    setLoading(prev => ({ ...prev, [type]: true }));
    setMessage(null);

    try {
      let response;
      switch (type) {
        case '1c':
          response = await importsApi.import1C(file);
          break;
        case 'wb-barcodes':
          response = await importsApi.importWBBarcodes(file);
          break;
        case 'wb-prices':
          response = await importsApi.importWBPrices(file);
          break;
        case 'wb-min-prices':
          response = await importsApi.importWBMinPrices(file);
          break;
        case 'ozon-barcodes':
          response = await importsApi.importOzonBarcodes(file);
          break;
        case 'ozon-prices':
          response = await importsApi.importOzonPrices(file);
          break;
        default:
          break;
      }

      setMessage({
        type: 'success',
        text: `Импорт завершен! Обработано: ${response.data.records_processed}, Добавлено: ${response.data.records_added}, Обновлено: ${response.data.records_updated}, Ошибок: ${response.data.records_failed}`
      });
      
      loadLogs();
    } catch (err) {
      setMessage({
        type: 'error',
        text: `Ошибка импорта: ${err.response?.data?.detail || err.message}`
      });
    } finally {
      setLoading(prev => ({ ...prev, [type]: false }));
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'success':
        return 'success';
      case 'partial':
        return 'warning';
      case 'failed':
        return 'error';
      default:
        return 'default';
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Импорт данных
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
        {/* Импорт 1С */}
        <Grid item xs={12} md={6}>
          <ImportCard
            title="Данные из 1С"
            description="Загрузите файл с остатками, ценами и артикулами из 1С"
            onUpload={(file) => handleImport('1c', file)}
            loading={loading['1c']}
          />
        </Grid>

        {/* Wildberries */}
        <Grid item xs={12} md={6}>
          <ImportCard
            title="ШК Wildberries"
            description="Таблица с штрихкодами и артикулами WB"
            onUpload={(file) => handleImport('wb-barcodes', file)}
            loading={loading['wb-barcodes']}
          />
        </Grid>

        <Grid item xs={12} md={6}>
          <ImportCard
            title="Цены Wildberries"
            description="Текущие цены и скидки WB"
            onUpload={(file) => handleImport('wb-prices', file)}
            loading={loading['wb-prices']}
          />
        </Grid>

        <Grid item xs={12} md={6}>
          <ImportCard
            title="Минимальные цены Wildberries"
            description="Минимальные цены для автоакций WB"
            onUpload={(file) => handleImport('wb-min-prices', file)}
            loading={loading['wb-min-prices']}
          />
        </Grid>

        {/* Ozon */}
        <Grid item xs={12} md={6}>
          <ImportCard
            title="ШК Ozon"
            description="Таблица с штрихкодами и SKU Ozon"
            onUpload={(file) => handleImport('ozon-barcodes', file)}
            loading={loading['ozon-barcodes']}
          />
        </Grid>

        <Grid item xs={12} md={6}>
          <ImportCard
            title="Цены Ozon"
            description="Текущие цены и скидки Ozon"
            onUpload={(file) => handleImport('ozon-prices', file)}
            loading={loading['ozon-prices']}
          />
        </Grid>
      </Grid>

      {/* История импортов */}
      <Paper sx={{ mt: 4, p: 2 }}>
        <Typography variant="h6" gutterBottom>
          История импортов
        </Typography>
        <List>
          {logs.map((log) => (
            <ListItem
              key={log.id}
              divider
              sx={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
              }}
            >
              <Box sx={{ flex: 1 }}>
                <ListItemText
                  primary={`${log.source} - ${log.file_name || 'без имени'}`}
                  secondary={`Обработано: ${log.records_processed} | Добавлено: ${log.records_added} | Обновлено: ${log.records_updated} | Ошибок: ${log.records_failed}`}
                />
                <Typography variant="caption" color="text.secondary">
                  {new Date(log.created_at).toLocaleString('ru-RU')}
                </Typography>
              </Box>
              <Chip 
                label={log.status} 
                color={getStatusColor(log.status)}
                size="small"
              />
            </ListItem>
          ))}
        </List>
      </Paper>
    </Box>
  );
};

export default ImportPage;