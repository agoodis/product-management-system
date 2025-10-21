import React, { useState, useEffect, useCallback } from 'react';
import { AgGridReact } from 'ag-grid-react';
import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-alpine.css';
import { productsApi } from '../services/api';
import {
  Box,
  Button,
  TextField,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  CircularProgress,
  Alert
} from '@mui/material';

const ProductsTable = () => {
  const [rowData, setRowData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [brands, setBrands] = useState([]);
  const [categories, setCategories] = useState([]);
  const [filters, setFilters] = useState({
    search: '',
    brand: '',
    product_category: '',
    page: 1,
    page_size: 100
  });
  const [totalPages, setTotalPages] = useState(0);

  const columnDefs = [
    { 
      field: 'barcode', 
      headerName: 'Штрихкод', 
      filter: true, 
      pinned: 'left',
      width: 150
    },
    { field: 'article_1c', headerName: 'Артикул 1С', filter: true, width: 120 },
    { 
      field: 'name', 
      headerName: 'Название', 
      filter: true, 
      width: 250,
      editable: true 
    },
    { field: 'brand', headerName: 'Бренд', filter: true, width: 120 },
    { field: 'product_category', headerName: 'Категория', filter: true, width: 150 },
    { field: 'size', headerName: 'Размер', width: 100 },
    { 
      field: 'stock_total', 
      headerName: 'Остаток общий', 
      width: 130,
      type: 'numericColumn',
      editable: true
    },
    { 
      field: 'purchase_price', 
      headerName: 'Закупочная цена', 
      width: 140,
      type: 'numericColumn',
      editable: true,
      valueFormatter: params => params.value ? `${params.value.toFixed(2)} ₽` : ''
    },
    { field: 'season', headerName: 'Сезон', width: 100 },
    { field: 'collection', headerName: 'Коллекция', width: 120 },
    {
      headerName: 'WB',
      children: [
        {
          field: 'marketplace_data',
          headerName: 'Цена',
          width: 110,
          valueGetter: params => {
            const wb = params.data.marketplace_data?.find(m => m.marketplace === 'wb');
            return wb?.current_price || '';
          },
          valueFormatter: params => params.value ? `${params.value} ₽` : '-'
        },
        {
          field: 'marketplace_data',
          headerName: 'Скидка %',
          width: 110,
          valueGetter: params => {
            const wb = params.data.marketplace_data?.find(m => m.marketplace === 'wb');
            return wb?.discount_percent || '';
          },
          valueFormatter: params => params.value ? `${params.value}%` : '-'
        }
      ]
    },
    {
      headerName: 'Ozon',
      children: [
        {
          field: 'marketplace_data',
          headerName: 'Цена',
          width: 110,
          valueGetter: params => {
            const ozon = params.data.marketplace_data?.find(m => m.marketplace === 'ozon');
            return ozon?.current_price || '';
          },
          valueFormatter: params => params.value ? `${params.value} ₽` : '-'
        },
        {
          field: 'marketplace_data',
          headerName: 'Скидка %',
          width: 110,
          valueGetter: params => {
            const ozon = params.data.marketplace_data?.find(m => m.marketplace === 'ozon');
            return ozon?.discount_percent || '';
          },
          valueFormatter: params => params.value ? `${params.value}%` : '-'
        }
      ]
    },
    {
      headerName: 'Расчеты',
      children: [
        {
          field: 'calculated_data.margin_percent',
          headerName: 'Наценка %',
          width: 120,
          valueFormatter: params => params.value ? `${params.value.toFixed(1)}%` : '-'
        },
        {
          field: 'calculated_data.turnover_rate',
          headerName: 'Оборачиваемость',
          width: 150,
          valueFormatter: params => params.value ? params.value.toFixed(2) : '-'
        }
      ]
    }
  ];

  const defaultColDef = {
    sortable: true,
    resizable: true,
    filter: true,
  };

  const loadProducts = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await productsApi.getAll(filters);
      setRowData(response.data.items);
      setTotalPages(response.data.total_pages);
    } catch (err) {
      setError('Ошибка загрузки товаров: ' + err.message);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  const loadFilters = useCallback(async () => {
    try {
      const [brandsRes, categoriesRes] = await Promise.all([
        productsApi.getBrands(),
        productsApi.getCategories()
      ]);
      setBrands(brandsRes.data);
      setCategories(categoriesRes.data);
    } catch (err) {
      console.error('Ошибка загрузки фильтров:', err);
    }
  }, []);

  useEffect(() => {
    loadProducts();
  }, [loadProducts]);

  useEffect(() => {
    loadFilters();
  }, [loadFilters]);

  const handleCellValueChanged = async (params) => {
    try {
      const barcode = params.data.barcode;
      const field = params.colDef.field;
      const newValue = params.newValue;
      
      await productsApi.update(barcode, { [field]: newValue });
    } catch (err) {
      setError('Ошибка обновления товара: ' + err.message);
      loadProducts(); // Перезагружаем данные
    }
  };

  const handleFilterChange = (field, value) => {
    setFilters(prev => ({ ...prev, [field]: value, page: 1 }));
  };

  const handlePageChange = (newPage) => {
    setFilters(prev => ({ ...prev, page: newPage }));
  };

  return (
    <Box sx={{ width: '100%', height: '100%' }}>
      {/* Фильтры */}
      <Box sx={{ mb: 2, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
        <TextField
          label="Поиск"
          variant="outlined"
          size="small"
          value={filters.search}
          onChange={(e) => handleFilterChange('search', e.target.value)}
          placeholder="Название, штрихкод, артикул..."
          sx={{ minWidth: 300 }}
        />
        
        <FormControl size="small" sx={{ minWidth: 150 }}>
          <InputLabel>Бренд</InputLabel>
          <Select
            value={filters.brand}
            onChange={(e) => handleFilterChange('brand', e.target.value)}
            label="Бренд"
          >
            <MenuItem value="">Все</MenuItem>
            {brands.map(brand => (
              <MenuItem key={brand} value={brand}>{brand}</MenuItem>
            ))}
          </Select>
        </FormControl>

        <FormControl size="small" sx={{ minWidth: 150 }}>
          <InputLabel>Категория</InputLabel>
          <Select
            value={filters.product_category}
            onChange={(e) => handleFilterChange('product_category', e.target.value)}
            label="Категория"
          >
            <MenuItem value="">Все</MenuItem>
            {categories.map(category => (
              <MenuItem key={category} value={category}>{category}</MenuItem>
            ))}
          </Select>
        </FormControl>

        <Button 
          variant="outlined" 
          onClick={loadProducts}
          disabled={loading}
        >
          Обновить
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {loading && <CircularProgress />}

      {/* Таблица */}
      <div className="ag-theme-alpine" style={{ height: 'calc(100vh - 250px)', width: '100%' }}>
        <AgGridReact
          rowData={rowData}
          columnDefs={columnDefs}
          defaultColDef={defaultColDef}
          onCellValueChanged={handleCellValueChanged}
          pagination={false}
          rowSelection="multiple"
          enableRangeSelection={true}
          suppressRowClickSelection={true}
        />
      </div>

      {/* Пагинация */}
      <Box sx={{ mt: 2, display: 'flex', justifyContent: 'center', gap: 2, alignItems: 'center' }}>
        <Button 
          disabled={filters.page === 1}
          onClick={() => handlePageChange(filters.page - 1)}
        >
          Назад
        </Button>
        <span>Страница {filters.page} из {totalPages}</span>
        <Button 
          disabled={filters.page >= totalPages}
          onClick={() => handlePageChange(filters.page + 1)}
        >
          Вперед
        </Button>
      </Box>
    </Box>
  );
};

export default ProductsTable;