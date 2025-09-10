import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  IconButton,
  Pagination,
  Grid,
  Card,
  CardContent,
} from '@mui/material';
import { Search, Refresh } from '@mui/icons-material';
import { useQuery } from 'react-query';
import { format } from 'date-fns';

import { vulnerabilityApi } from '../services/api';
import { Vulnerability } from '../types';

const COLORS = {
  CRITICAL: '#f44336',
  HIGH: '#ff9800',
  MEDIUM: '#ffeb3b',
  LOW: '#4caf50',
  INFO: '#2196f3',
};

const Vulnerabilities: React.FC = () => {
  const [page, setPage] = useState(1);
  const [limit] = useState(25);
  const [searchQuery, setSearchQuery] = useState('');
  const [severityFilter, setSeverityFilter] = useState('');
  const [toolFilter, setToolFilter] = useState('');

  const offset = (page - 1) * limit;

  // Fetch vulnerabilities based on current filters
  const { data: vulnerabilitiesData, isLoading, refetch } = useQuery(
    ['vulnerabilities', page, searchQuery, severityFilter, toolFilter],
    () => {
      if (searchQuery) {
        return vulnerabilityApi.search({
          q: searchQuery,
          severity: severityFilter || undefined,
          tool: toolFilter || undefined,
          limit,
          offset,
        });
      } else {
        return vulnerabilityApi.getLatest({
          severity: severityFilter || undefined,
          tool: toolFilter || undefined,
          limit,
          offset,
          hours: 168, // Last week
        });
      }
    },
    { refetchInterval: 60000 } // Refetch every minute
  );

  const handlePageChange = (_: React.ChangeEvent<unknown>, value: number) => {
    setPage(value);
  };

  const getSeverityColor = (severity: string) => {
    return COLORS[severity as keyof typeof COLORS] || '#9e9e9e';
  };

  const formatDate = (dateString: string) => {
    return format(new Date(dateString), 'MMM dd, yyyy HH:mm');
  };

  const totalPages = Math.ceil((vulnerabilitiesData?.total || 0) / limit);

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Vulnerabilities
        </Typography>
        <IconButton onClick={() => refetch()}>
          <Refresh />
        </IconButton>
      </Box>

      {/* Filters */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} md={4}>
          <TextField
            fullWidth
            placeholder="Search vulnerabilities..."
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              setPage(1);
            }}
            InputProps={{
              startAdornment: <Search sx={{ mr: 1, color: 'action.active' }} />,
            }}
          />
        </Grid>
        <Grid item xs={12} md={3}>
          <FormControl fullWidth>
            <InputLabel>Severity</InputLabel>
            <Select
              value={severityFilter}
              onChange={(e) => {
                setSeverityFilter(e.target.value);
                setPage(1);
              }}
              label="Severity"
            >
              <MenuItem value="">All</MenuItem>
              <MenuItem value="CRITICAL">Critical</MenuItem>
              <MenuItem value="HIGH">High</MenuItem>
              <MenuItem value="MEDIUM">Medium</MenuItem>
              <MenuItem value="LOW">Low</MenuItem>
              <MenuItem value="INFO">Info</MenuItem>
            </Select>
          </FormControl>
        </Grid>
        <Grid item xs={12} md={3}>
          <FormControl fullWidth>
            <InputLabel>Tool</InputLabel>
            <Select
              value={toolFilter}
              onChange={(e) => {
                setToolFilter(e.target.value);
                setPage(1);
              }}
              label="Tool"
            >
              <MenuItem value="">All Tools</MenuItem>
              <MenuItem value="cursor">Cursor</MenuItem>
              <MenuItem value="github_copilot">GitHub Copilot</MenuItem>
              <MenuItem value="amazon_codewhisperer">CodeWhisperer</MenuItem>
              <MenuItem value="tabnine">Tabnine</MenuItem>
              <MenuItem value="codeium">Codeium</MenuItem>
            </Select>
          </FormControl>
        </Grid>
      </Grid>

      {/* Summary */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Found
              </Typography>
              <Typography variant="h5">
                {vulnerabilitiesData?.total || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Critical
              </Typography>
              <Typography variant="h5" sx={{ color: COLORS.CRITICAL }}>
                {vulnerabilitiesData?.vulnerabilities?.filter(v => v.severity === 'CRITICAL').length || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Unpatched
              </Typography>
              <Typography variant="h5" sx={{ color: COLORS.HIGH }}>
                {vulnerabilitiesData?.vulnerabilities?.filter(v => v.patch_status === 'unpatched').length || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                With Exploits
              </Typography>
              <Typography variant="h5" sx={{ color: COLORS.CRITICAL }}>
                {vulnerabilitiesData?.vulnerabilities?.filter(v => v.exploit_in_wild).length || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Vulnerabilities Table */}
      <Paper>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>ID</TableCell>
                <TableCell>Title</TableCell>
                <TableCell>Severity</TableCell>
                <TableCell>CVSS</TableCell>
                <TableCell>Tools</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Discovered</TableCell>
                <TableCell>Exploit</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={8} align="center">
                    Loading...
                  </TableCell>
                </TableRow>
              ) : vulnerabilitiesData?.vulnerabilities?.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} align="center">
                    No vulnerabilities found
                  </TableCell>
                </TableRow>
              ) : (
                vulnerabilitiesData?.vulnerabilities?.map((vuln: Vulnerability) => (
                  <TableRow key={vuln.id} hover>
                    <TableCell>
                      <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                        {vuln.cve_id || vuln.vulnerability_id}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" sx={{ maxWidth: 300 }}>
                        {vuln.title}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={vuln.severity}
                        size="small"
                        sx={{
                          backgroundColor: getSeverityColor(vuln.severity),
                          color: 'white',
                          fontWeight: 'bold',
                        }}
                      />
                    </TableCell>
                    <TableCell>
                      {vuln.cvss_score ? (
                        <Typography
                          variant="body2"
                          sx={{
                            fontWeight: 'bold',
                            color: getSeverityColor(vuln.severity),
                          }}
                        >
                          {vuln.cvss_score.toFixed(1)}
                        </Typography>
                      ) : (
                        '-'
                      )}
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {vuln.affected_tools.slice(0, 2).map((tool) => (
                          <Chip
                            key={tool}
                            label={tool}
                            size="small"
                            variant="outlined"
                          />
                        ))}
                        {vuln.affected_tools.length > 2 && (
                          <Chip
                            label={`+${vuln.affected_tools.length - 2}`}
                            size="small"
                            variant="outlined"
                          />
                        )}
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={vuln.patch_status.replace('_', ' ')}
                        size="small"
                        color={vuln.patch_status === 'patched' ? 'success' : 
                               vuln.patch_status === 'patch_available' ? 'warning' : 'error'}
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" color="textSecondary">
                        {formatDate(vuln.discovery_date || vuln.created_at)}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      {vuln.exploit_in_wild && (
                        <Chip label="Wild" size="small" color="error" />
                      )}
                      {vuln.poc_available && !vuln.exploit_in_wild && (
                        <Chip label="PoC" size="small" color="warning" />
                      )}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>

        {/* Pagination */}
        {totalPages > 1 && (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 2 }}>
            <Pagination
              count={totalPages}
              page={page}
              onChange={handlePageChange}
              color="primary"
              showFirstButton
              showLastButton
            />
          </Box>
        )}
      </Paper>
    </Box>
  );
};

export default Vulnerabilities;