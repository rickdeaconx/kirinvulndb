import React from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip,
  Divider,
} from '@mui/material';
import {
  Settings as SettingsIcon,
  Security,
  Storage,
  Cloud,
  Speed,
  CheckCircle,
  Error,
  Warning,
} from '@mui/icons-material';
import { useQuery } from 'react-query';

import { healthApi } from '../services/api';

const Settings: React.FC = () => {
  // Fetch system health and configuration
  const { data: health, isLoading } = useQuery(
    'detailedHealth',
    () => healthApi.detailed(),
    { refetchInterval: 30000 }
  );

  const { data: metrics } = useQuery(
    'systemMetrics',
    () => healthApi.metrics(),
    { refetchInterval: 10000 }
  );

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'healthy':
      case 'success':
        return <CheckCircle sx={{ color: '#4caf50' }} />;
      case 'unhealthy':
      case 'error':
        return <Error sx={{ color: '#f44336' }} />;
      case 'warning':
        return <Warning sx={{ color: '#ff9800' }} />;
      default:
        return <Security />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'healthy':
      case 'success':
        return 'success';
      case 'unhealthy':
      case 'error':
        return 'error';
      case 'warning':
        return 'warning';
      default:
        return 'default';
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Settings & Status
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* System Overview */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              System Overview
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6} md={3}>
                <Card>
                  <CardContent>
                    <Typography color="textSecondary" gutterBottom>
                      Service Status
                    </Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      {getStatusIcon(health?.status || 'unknown')}
                      <Typography variant="h6">
                        {health?.status || 'Unknown'}
                      </Typography>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Card>
                  <CardContent>
                    <Typography color="textSecondary" gutterBottom>
                      Version
                    </Typography>
                    <Typography variant="h6">
                      {health?.version || '1.0.0'}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Card>
                  <CardContent>
                    <Typography color="textSecondary" gutterBottom>
                      Uptime
                    </Typography>
                    <Typography variant="h6">
                      {metrics?.uptime || '0d 0h 0m'}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Card>
                  <CardContent>
                    <Typography color="textSecondary" gutterBottom>
                      Active Connections
                    </Typography>
                    <Typography variant="h6">
                      {metrics?.active_websockets || 0}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Paper>
        </Grid>

        {/* Component Health */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Component Health
            </Typography>
            <List>
              {health?.checks && Object.entries(health.checks).map(([component, status]: [string, any]) => (
                <ListItem key={component}>
                  <ListItemIcon>
                    {component === 'database' && <Storage />}
                    {component === 'redis' && <Speed />}
                    {component === 'kafka' && <Cloud />}
                    {!['database', 'redis', 'kafka'].includes(component) && <Security />}
                  </ListItemIcon>
                  <ListItemText
                    primary={component.charAt(0).toUpperCase() + component.slice(1)}
                    secondary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Chip
                          label={status.status}
                          size="small"
                          color={getStatusColor(status.status) as any}
                          variant="outlined"
                        />
                        {status.response_time && (
                          <Typography variant="caption" color="textSecondary">
                            {status.response_time}
                          </Typography>
                        )}
                        {status.error && (
                          <Typography variant="caption" color="error">
                            {status.error}
                          </Typography>
                        )}
                      </Box>
                    }
                  />
                </ListItem>
              ))}
            </List>
          </Paper>
        </Grid>

        {/* Configuration */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Configuration
            </Typography>
            <List>
              <ListItem>
                <ListItemIcon>
                  <SettingsIcon />
                </ListItemIcon>
                <ListItemText
                  primary="Collection Intervals"
                  secondary={
                    <Box>
                      <Typography variant="body2">CVE: 5 minutes</Typography>
                      <Typography variant="body2">Vendors: 10 minutes</Typography>
                      <Typography variant="body2">Community: 1 hour</Typography>
                    </Box>
                  }
                />
              </ListItem>
              <Divider />
              <ListItem>
                <ListItemIcon>
                  <Security />
                </ListItemIcon>
                <ListItemText
                  primary="Monitored Tools"
                  secondary="8 AI coding assistants actively monitored"
                />
              </ListItem>
              <Divider />
              <ListItem>
                <ListItemIcon>
                  <Cloud />
                </ListItemIcon>
                <ListItemText
                  primary="Data Sources"
                  secondary={
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 1 }}>
                      <Chip label="NVD" size="small" variant="outlined" />
                      <Chip label="GitHub" size="small" variant="outlined" />
                      <Chip label="RSS Feeds" size="small" variant="outlined" />
                      <Chip label="Vendor APIs" size="small" variant="outlined" />
                    </Box>
                  }
                />
              </ListItem>
            </List>
          </Paper>
        </Grid>

        {/* System Information */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              System Information
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" gutterBottom>
                  Service Details
                </Typography>
                <List dense>
                  <ListItem>
                    <ListItemText
                      primary="Service Name"
                      secondary={health?.service || 'Kirin Vulnerability Database'}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText
                      primary="Last Started"
                      secondary={health?.timestamp ? new Date(health.timestamp).toLocaleString() : 'Unknown'}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText
                      primary="Environment"
                      secondary="Production"
                    />
                  </ListItem>
                </List>
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" gutterBottom>
                  Performance Metrics
                </Typography>
                <List dense>
                  <ListItem>
                    <ListItemText
                      primary="Total Requests"
                      secondary={metrics?.requests_total || 0}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText
                      primary="Database Connections"
                      secondary={metrics?.database_connections || 0}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText
                      primary="Memory Usage"
                      secondary="Normal"
                    />
                  </ListItem>
                </List>
              </Grid>
            </Grid>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Settings;