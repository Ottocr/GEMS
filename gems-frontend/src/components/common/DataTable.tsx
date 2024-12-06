import React, { ReactNode } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Paper,
  Box,
  Typography,
  TextField,
  InputAdornment,
  IconButton,
  Tooltip,
  CircularProgress,
} from '@mui/material';
import {
  Search as SearchIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { TableColumn } from '../../types';

interface DataTableProps<T = any> {
  columns: TableColumn<T>[];
  data: T[];
  loading?: boolean;
  error?: string | null;
  searchEnabled?: boolean;
  refreshEnabled?: boolean;
  onRefresh?: () => void;
  rowsPerPageOptions?: number[];
  onRowClick?: (row: T) => void;
  emptyMessage?: string;
}

function DataTable<T extends Record<string, any>>({
  columns,
  data,
  loading = false,
  error = null,
  searchEnabled = true,
  refreshEnabled = true,
  onRefresh,
  rowsPerPageOptions = [10, 25, 50],
  onRowClick,
  emptyMessage = 'No data available',
}: DataTableProps<T>): JSX.Element {
  const [page, setPage] = React.useState(0);
  const [rowsPerPage, setRowsPerPage] = React.useState(rowsPerPageOptions[0]);
  const [searchTerm, setSearchTerm] = React.useState('');

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(+event.target.value);
    setPage(0);
  };

  const filteredData = React.useMemo(() => {
    if (!searchTerm) return data;

    return data.filter(row =>
      Object.values(row).some(value =>
        String(value).toLowerCase().includes(searchTerm.toLowerCase())
      )
    );
  }, [data, searchTerm]);

  const displayData = filteredData.slice(
    page * rowsPerPage,
    page * rowsPerPage + rowsPerPage
  );

  const renderCellContent = (column: TableColumn<T>, row: T): ReactNode => {
    const value = row[column.id as keyof T];
    return column.format ? column.format(value, row) : String(value);
  };

  return (
    <Paper sx={{ width: '100%', overflow: 'hidden' }}>
      {/* Table Controls */}
      {(searchEnabled || refreshEnabled) && (
        <Box sx={{ p: 2, display: 'flex', alignItems: 'center', gap: 2 }}>
          {searchEnabled && (
            <TextField
              size="small"
              placeholder="Search..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
              }}
              sx={{ minWidth: 200 }}
            />
          )}
          {refreshEnabled && (
            <Tooltip title="Refresh data">
              <IconButton 
                onClick={onRefresh}
                disabled={loading}
              >
                <RefreshIcon />
              </IconButton>
            </Tooltip>
          )}
          {loading && <CircularProgress size={24} />}
        </Box>
      )}

      {/* Error Message */}
      {error && (
        <Box sx={{ p: 2, color: 'error.main' }}>
          <Typography variant="body2">{error}</Typography>
        </Box>
      )}

      {/* Table */}
      <TableContainer sx={{ maxHeight: 440 }}>
        <Table stickyHeader>
          <TableHead>
            <TableRow>
              {columns.map((column) => (
                <TableCell
                  key={column.id}
                  align={column.align}
                  style={{ minWidth: column.minWidth }}
                >
                  {column.label}
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {displayData.length > 0 ? (
              displayData.map((row, index) => (
                <TableRow
                  hover
                  key={index}
                  onClick={() => onRowClick && onRowClick(row)}
                  sx={{ cursor: onRowClick ? 'pointer' : 'default' }}
                >
                  {columns.map((column) => (
                    <TableCell key={column.id} align={column.align}>
                      {renderCellContent(column, row)}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell 
                  colSpan={columns.length} 
                  align="center"
                  sx={{ py: 4 }}
                >
                  <Typography variant="body2" color="text.secondary">
                    {loading ? 'Loading...' : emptyMessage}
                  </Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Pagination */}
      <TablePagination
        rowsPerPageOptions={rowsPerPageOptions}
        component="div"
        count={filteredData.length}
        rowsPerPage={rowsPerPage}
        page={page}
        onPageChange={handleChangePage}
        onRowsPerPageChange={handleChangeRowsPerPage}
      />
    </Paper>
  );
}

export default DataTable;
export type { TableColumn };
