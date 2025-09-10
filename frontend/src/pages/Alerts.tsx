import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemSecondaryAction,
  IconButton,
  Chip,
  Button,
  Grid,
  Card,
  CardContent,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Pagination,
} from '@mui/material';
import {
  Error,
  Warning,
  Info,
  CheckCircle,
  Refresh,
  Check,
  Close,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { format } from 'date-fns';
import toast from 'react-hot-toast';

import { alertsApi } from '../services/api';
import { Alert } from '../types';

const PRIORITY_ICONS = {
  critical: <Error sx={{ color: '#f44336' }} />,
  high: <Warning sx={{ color: '#ff9800' }} />,
  medium: <Info sx={{ color: '#2196f3' }} />,
  low: <CheckCircle sx={{ color: '#4caf50' }} />,
};

const PRIORITY_COLORS = {
  critical: '#f44336',
  high: '#ff9800', 
  medium: '#2196f3',
  low: '#4caf50',
};

const Alerts: React.FC = () => {
  const [page, setPage] = useState(1);
  const [limit] = useState(25);
  const [statusFilter, setStatusFilter] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');
  const queryClient = useQueryClient();

  const offset = (page - 1) * limit;

  // Fetch alerts
  const { data: alertsData, isLoading, refetch } = useQuery(
    ['alerts', page, statusFilter, priorityFilter],
    () => alertsApi.getAll({
      status: statusFilter || undefined,
      priority: priorityFilter || undefined,
      hours: 168, // Last week
      limit,
      offset,
    }),
    { refetchInterval: 30000 }
  );

  // Fetch alert statistics
  const { data: alertStats } = useQuery(
    'alertStats',
    () => alertsApi.getStats(7),
    { refetchInterval: 60000 }
  );

  // Acknowledge alert mutation
  const acknowledgeMutation = useMutation(
    (alertId: string) => alertsApi.acknowledge(alertId),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('alerts');
        toast.success('Alert acknowledged');
      },
      onError: () => {
        toast.error('Failed to acknowledge alert');
      },
    }
  );

  // Resolve alert mutation
  const resolveMutation = useMutation(
    (alertId: string) => alertsApi.resolve(alertId),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('alerts');
        toast.success('Alert resolved');
      },
      onError: () => {
        toast.error('Failed to resolve alert');
      },
    }
  );

  const handlePageChange = (_: React.ChangeEvent<unknown>, value: number) => {
    setPage(value);
  };

  const getPriorityIcon = (priority: string) => {
    return PRIORITY_ICONS[priority as keyof typeof PRIORITY_ICONS] || <Info />;
  };

  const getPriorityColor = (priority: string) => {
    return PRIORITY_COLORS[priority as keyof typeof PRIORITY_COLORS] || '#666666';
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending':
        return 'warning';
      case 'acknowledged':
        return 'info';
      case 'resolved':
        return 'success';
      case 'suppressed':
        return 'default';
      default:
        return 'default';
    }
  };

  const formatAlertType = (type: string) => {
    return type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  const totalPages = Math.ceil((alertsData?.total || 0) / limit);

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Security Alerts
        </Typography>
        <IconButton onClick={() => refetch()}>
          <Refresh />
        </IconButton>
      </Box>

      {/* Summary Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Alerts
              </Typography>
              <Typography variant="h5">
                {alertsData?.total || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Pending
              </Typography>
              <Typography variant="h5" sx={{ color: PRIORITY_COLORS.high }}>
                {alertStats?.status_distribution?.pending || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Critical Priority
              </Typography>
              <Typography variant="h5" sx={{ color: PRIORITY_COLORS.critical }}>
                {alertStats?.priority_distribution?.critical || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Resolved
              </Typography>
              <Typography variant="h5" sx={{ color: PRIORITY_COLORS.low }}>
                {alertStats?.status_distribution?.resolved || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Filters */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} md={4}>
          <FormControl fullWidth>
            <InputLabel>Status</InputLabel>
            <Select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
              label="Status"
            >
              <MenuItem value="">All Statuses</MenuItem>
              <MenuItem value="pending">Pending</MenuItem>
              <MenuItem value="acknowledged">Acknowledged</MenuItem>
              <MenuItem value="resolved">Resolved</MenuItem>
              <MenuItem value="suppressed">Suppressed</MenuItem>
            </Select>
          </FormControl>
        </Grid>
        <Grid item xs={12} md={4}>
          <FormControl fullWidth>
            <InputLabel>Priority</InputLabel>
            <Select
              value={priorityFilter}
              onChange={(e) => {
                setPriorityFilter(e.target.value);
                setPage(1);
              }}
              label="Priority"
            >
              <MenuItem value="">All Priorities</MenuItem>
              <MenuItem value="critical">Critical</MenuItem>
              <MenuItem value="high">High</MenuItem>
              <MenuItem value="medium">Medium</MenuItem>
              <MenuItem value="low">Low</MenuItem>
            </Select>
          </FormControl>
        </Grid>
      </Grid>

      {/* Alerts List */}
      <Paper>
        <List>
          {isLoading ? (
            <ListItem>
              <ListItemText primary="Loading alerts..." />
            </ListItem>
          ) : alertsData?.alerts?.length === 0 ? (
            <ListItem>
              <ListItemText 
                primary="No alerts found"
                secondary="All systems are running normally"
              />
            </ListItem>
          ) : (
            alertsData?.alerts?.map((alert: Alert, index: number) => (
              <React.Fragment key={alert.id}>
                <ListItem
                  sx={{
                    borderLeft: `4px solid ${getPriorityColor(alert.priority)}`,
                    bgcolor: alert.status === 'pending' ? 'rgba(255, 193, 7, 0.1)' : 'transparent',
                  }}
                >
                  <ListItemIcon>
                    {getPriorityIcon(alert.priority)}
                  </ListItemIcon>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="subtitle1">
                          {alert.title}
                        </Typography>
                        <Chip
                          label={alert.priority}
                          size="small"
                          sx={{
                            backgroundColor: getPriorityColor(alert.priority),
                            color: 'white',
                          }}
                        />
                        <Chip
                          label={alert.status}
                          size="small"
                          color={getStatusColor(alert.status) as any}
                          variant="outlined"
                        />
                      </Box>
                    }
                    secondary={
                      <Box>
                        <Typography variant="body2" color="textSecondary" sx={{ mb: 1 }}>
                          {alert.message}
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                          <Chip
                            label={formatAlertType(alert.alert_type)}
                            size="small"
                            variant="outlined"
                          />
                          <Typography variant="caption" color="textSecondary">
                            {format(new Date(alert.created_at), 'MMM dd, yyyy HH:mm')}
                          </Typography>
                          {alert.acknowledged_time && (
                            <Typography variant="caption" color="success.main">
                              • Acknowledged {format(new Date(alert.acknowledged_time), 'MMM dd, HH:mm')}
                            </Typography>
                          )}
                        </Box>
                      </Box>
                    }
                  />
                  <ListItemSecondaryAction>
                    <Box sx={{ display: 'flex', gap: 1 }}>
                      {alert.status === 'pending' && (
                        <>
                          <IconButton
                            size="small"
                            color="primary"
                            onClick={() => acknowledgeMutation.mutate(alert.id)}
                            disabled={acknowledgeMutation.isLoading}
                          >
                            <Check />
                          </IconButton>
                          <IconButton
                            size="small"
                            color="success"
                            onClick={() => resolveMutation.mutate(alert.id)}
                            disabled={resolveMutation.isLoading}
                          >
                            <CheckCircle />
                          </IconButton>
                        </>
                      )}
                      {alert.status === 'acknowledged' && (
                        <IconButton
                          size="small"
                          color="success"
                          onClick={() => resolveMutation.mutate(alert.id)}
                          disabled={resolveMutation.isLoading}
                        >
                          <CheckCircle />
                        </IconButton>
                      )}
                    </Box>
                  </ListItemSecondaryAction>
                </ListItem>
                {index < (alertsData?.alerts?.length || 0) - 1 && (
                  <Box sx={{ mx: 2 }}>
                    <hr style={{ border: 'none', borderTop: '1px solid rgba(255,255,255,0.1)' }} />
                  </Box>
                )}
              </React.Fragment>
            ))
          )}
        </List>

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

export default Alerts;