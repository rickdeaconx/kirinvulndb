import React from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  Chip,
  Avatar,
  LinearProgress,
  IconButton,
  Divider,
} from '@mui/material';
import { Refresh, Security, BugReport, CheckCircle } from '@mui/icons-material';
import { useQuery } from 'react-query';

import { toolsApi } from '../services/api';

const Tools: React.FC = () => {
  const { data: toolsData, isLoading, refetch } = useQuery(
    'tools',
    () => toolsApi.getAll({ active_only: true }),
    { refetchInterval: 60000 }
  );

  const getVendorColor = (vendor: string) => {
    const colors: Record<string, string> = {
      'GitHub/Microsoft': '#0066cc',
      'Cursor Inc.': '#8b5cf6',
      'Amazon Web Services': '#ff9900',
      'Tabnine Ltd.': '#1976d2',
      'Exafunction Inc.': '#00c853',
      'Replit Inc.': '#f57c00',
      'Sourcegraph Inc.': '#00b4d8',
      'JetBrains': '#000000',
    };
    return colors[vendor] || '#666666';
  };

  const getRiskLevel = (critical: number, total: number) => {
    if (critical > 5) return { level: 'High', color: 'error' };
    if (critical > 2) return { level: 'Medium', color: 'warning' };
    if (total > 0) return { level: 'Low', color: 'info' };
    return { level: 'None', color: 'success' };
  };

  if (isLoading) {
    return (
      <Box>
        <Typography variant="h4" gutterBottom>
          AI Tools
        </Typography>
        <LinearProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          AI Coding Tools
        </Typography>
        <IconButton onClick={() => refetch()}>
          <Refresh />
        </IconButton>
      </Box>

      <Typography variant="body1" color="textSecondary" sx={{ mb: 3 }}>
        Monitoring {toolsData?.total || 0} AI coding assistants for security vulnerabilities
      </Typography>

      <Grid container spacing={3}>
        {toolsData?.tools?.map((tool) => {
          const risk = getRiskLevel(tool.critical_vulnerabilities, tool.total_vulnerabilities);
          
          return (
            <Grid item xs={12} sm={6} md={4} key={tool.id}>
              <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                <CardContent sx={{ flexGrow: 1 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Avatar
                      sx={{
                        bgcolor: getVendorColor(tool.vendor),
                        mr: 2,
                        width: 48,
                        height: 48,
                      }}
                    >
                      {tool.display_name.charAt(0)}
                    </Avatar>
                    <Box sx={{ flexGrow: 1 }}>
                      <Typography variant="h6" component="h2">
                        {tool.display_name}
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        {tool.vendor}
                      </Typography>
                    </Box>
                    <Chip
                      icon={<Security />}
                      label={tool.is_actively_monitored ? 'Monitored' : 'Inactive'}
                      color={tool.is_actively_monitored ? 'success' : 'default'}
                      size="small"
                    />
                  </Box>

                  {tool.description && (
                    <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                      {tool.description}
                    </Typography>
                  )}

                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Security Status
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
                      <Chip
                        label={`Risk: ${risk.level}`}
                        color={risk.color as any}
                        size="small"
                      />
                      {tool.current_version && (
                        <Chip
                          label={`v${tool.current_version}`}
                          variant="outlined"
                          size="small"
                        />
                      )}
                    </Box>
                  </Box>

                  <Divider sx={{ my: 2 }} />

                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                    <Box sx={{ textAlign: 'center' }}>
                      <Typography variant="h6" color="error">
                        {tool.critical_vulnerabilities}
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        Critical
                      </Typography>
                    </Box>
                    <Box sx={{ textAlign: 'center' }}>
                      <Typography variant="h6">
                        {tool.total_vulnerabilities}
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        Total
                      </Typography>
                    </Box>
                    <Box sx={{ textAlign: 'center' }}>
                      <Typography variant="h6" color="success.main">
                        {tool.total_vulnerabilities - tool.critical_vulnerabilities}
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        Other
                      </Typography>
                    </Box>
                  </Box>

                  {tool.supported_languages && (
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="subtitle2" gutterBottom>
                        Supported Languages
                      </Typography>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {tool.supported_languages.slice(0, 4).map((lang) => (
                          <Chip
                            key={lang}
                            label={lang}
                            size="small"
                            variant="outlined"
                          />
                        ))}
                        {tool.supported_languages.length > 4 && (
                          <Chip
                            label={`+${tool.supported_languages.length - 4}`}
                            size="small"
                            variant="outlined"
                          />
                        )}
                      </Box>
                    </Box>
                  )}

                  {tool.platform_support && (
                    <Box>
                      <Typography variant="subtitle2" gutterBottom>
                        Platforms
                      </Typography>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {tool.platform_support.slice(0, 3).map((platform) => (
                          <Chip
                            key={platform}
                            label={platform}
                            size="small"
                            variant="outlined"
                          />
                        ))}
                        {tool.platform_support.length > 3 && (
                          <Chip
                            label={`+${tool.platform_support.length - 3}`}
                            size="small"
                            variant="outlined"
                          />
                        )}
                      </Box>
                    </Box>
                  )}
                </CardContent>

                <CardActions>
                  <Button
                    size="small"
                    startIcon={<BugReport />}
                    onClick={() => {
                      // Navigate to tool vulnerabilities
                      window.location.href = `/vulnerabilities?tool=${tool.name}`;
                    }}
                  >
                    View Vulnerabilities
                  </Button>
                  {tool.total_vulnerabilities === 0 && (
                    <Button
                      size="small"
                      startIcon={<CheckCircle />}
                      color="success"
                      disabled
                    >
                      Clean
                    </Button>
                  )}
                </CardActions>
              </Card>
            </Grid>
          );
        })}
      </Grid>

      {toolsData?.tools?.length === 0 && (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <Typography variant="h6" color="textSecondary">
            No AI tools found
          </Typography>
          <Typography variant="body2" color="textSecondary">
            Check back later as we add more tools to monitor
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default Tools;