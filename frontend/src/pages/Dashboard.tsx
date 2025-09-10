import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Chip,
  List,
  ListItem,
  ListItemText,
  Avatar,
  LinearProgress,
  Paper,
  IconButton,
  Fade,
  Tooltip,
  Container,
} from '@mui/material';
import {
  Security,
  Warning,
  Error,
  CheckCircle,
  Computer,
  Timeline,
  Shield,
  BugReport,
  Code,
  Refresh,
  Speed,
  PlayArrow,
  Stop,
} from '@mui/icons-material';
import { useWebSocket } from '../services/websocket';

const apiService = {
  getVulnerabilities: () => fetch('/api/vulnerabilities/latest').then(res => res.json()),
  getTools: () => fetch('/api/tools/').then(res => res.json()),
};

interface Vulnerability {
  id: string;
  vulnerability_id: string;
  title: string;
  severity: string;
  cvss_score: number;
  affected_tools: string[];
  attack_vectors: string[];
  patch_status: string;
  discovery_date: string;
  created_at: string;
}

interface Tool {
  id: string;
  name: string;
  display_name: string;
  vendor: string;
  total_vulnerabilities: number;
  critical_vulnerabilities: number;
}

const Dashboard: React.FC = () => {
  const [vulnerabilities, setVulnerabilities] = useState<Vulnerability[]>([]);
  const [tools, setTools] = useState<Tool[]>([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    total: 0,
    critical: 0,
    high: 0,
    medium: 0,
    low: 0,
  });

  const { isConnected, lastMessage } = useWebSocket();

  const fetchData = async () => {
    try {
      setLoading(true);
      const [vulnResponse, toolsResponse] = await Promise.all([
        apiService.getVulnerabilities(),
        apiService.getTools(),
      ]);
      
      setVulnerabilities(vulnResponse.vulnerabilities || []);
      setTools(toolsResponse.tools || []);
      
      // Calculate stats
      const vulns = vulnResponse.vulnerabilities || [];
      const newStats = {
        total: vulns.length,
        critical: vulns.filter((v: Vulnerability) => v.severity === 'CRITICAL').length,
        high: vulns.filter((v: Vulnerability) => v.severity === 'HIGH').length,
        medium: vulns.filter((v: Vulnerability) => v.severity === 'MEDIUM').length,
        low: vulns.filter((v: Vulnerability) => v.severity === 'LOW').length,
      };
      setStats(newStats);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'CRITICAL': return '#ff1744';
      case 'HIGH': return '#ff9800';
      case 'MEDIUM': return '#ffeb3b';
      case 'LOW': return '#4caf50';
      case 'INFO': return '#2196f3';
      default: return '#757575';
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'CRITICAL': return <Error />;
      case 'HIGH': return <Warning />;
      case 'MEDIUM': return <Timeline />;
      case 'LOW': return <CheckCircle />;
      default: return <Security />;
    }
  };

  const StatCard = ({ title, value, icon, color, subtitle }: any) => (
    <Fade in={true} timeout={1000}>
      <Card 
        sx={{ 
          background: `linear-gradient(135deg, ${color}15 0%, ${color}05 100%)`,
          border: `1px solid ${color}30`,
          backdropFilter: 'blur(10px)',
          transition: 'all 0.3s ease',
          '&:hover': {
            transform: 'translateY(-4px)',
            boxShadow: `0 8px 25px ${color}25`,
            border: `1px solid ${color}50`,
          }
        }}
      >
        <CardContent>
          <Box display="flex" alignItems="center" justifyContent="space-between">
            <Box>
              <Typography variant="h3" sx={{ color, fontWeight: 700, mb: 0.5 }}>
                {value}
              </Typography>
              <Typography variant="h6" color="text.primary" fontWeight={500}>
                {title}
              </Typography>
              {subtitle && (
                <Typography variant="body2" color="text.secondary">
                  {subtitle}
                </Typography>
              )}
            </Box>
            <Avatar sx={{ bgcolor: `${color}20`, color, width: 56, height: 56 }}>
              {icon}
            </Avatar>
          </Box>
        </CardContent>
      </Card>
    </Fade>
  );

  return (
    <Box sx={{ p: 3, bgcolor: '#0a0a0a', minHeight: '100vh' }}>
      {/* Header */}
      <Box display="flex" justifyContent="between" alignItems="center" mb={4}>
        <Box>
          <Typography variant="h3" sx={{ 
            color: '#00ff88', 
            fontWeight: 700, 
            mb: 1,
            textShadow: '0 0 20px #00ff8850'
          }}>
            🛡️ Kirin Vulnerability Database
          </Typography>
          <Typography variant="h6" color="text.secondary">
            Real-time AI Code Security Monitoring
          </Typography>
        </Box>
        <Box display="flex" alignItems="center" gap={2}>
          <Tooltip title={isConnected ? "WebSocket Connected" : "WebSocket Disconnected"}>
            <Chip 
              icon={<Speed />}
              label={isConnected ? "LIVE" : "OFFLINE"}
              color={isConnected ? "success" : "error"}
              sx={{ 
                fontWeight: 700,
                animation: isConnected ? 'pulse 2s infinite' : 'none',
                '@keyframes pulse': {
                  '0%': { opacity: 1 },
                  '50%': { opacity: 0.7 },
                  '100%': { opacity: 1 },
                }
              }}
            />
          </Tooltip>
          <IconButton onClick={fetchData} sx={{ color: '#00ff88' }}>
            <Refresh />
          </IconButton>
        </Box>
      </Box>

      {/* Statistics Grid */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} sm={6} md={2.4}>
          <StatCard 
            title="Total Vulnerabilities" 
            value={stats.total} 
            icon={<BugReport />} 
            color="#00ff88"
            subtitle="All discovered issues"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <StatCard 
            title="Critical" 
            value={stats.critical} 
            icon={<Error />} 
            color="#ff1744"
            subtitle="Immediate action required"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <StatCard 
            title="High" 
            value={stats.high} 
            icon={<Warning />} 
            color="#ff9800"
            subtitle="High priority fixes"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <StatCard 
            title="Medium" 
            value={stats.medium} 
            icon={<Timeline />} 
            color="#ffeb3b"
            subtitle="Moderate risk"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <StatCard 
            title="AI Tools" 
            value={tools.length} 
            icon={<Computer />} 
            color="#2196f3"
            subtitle="Monitored platforms"
          />
        </Grid>
      </Grid>

      {/* Main Content Grid */}
      <Grid container spacing={3}>
        {/* Recent Vulnerabilities */}
        <Grid item xs={12} lg={8}>
          <Card sx={{ 
            bgcolor: 'rgba(255,255,255,0.02)',
            border: '1px solid rgba(0,255,136,0.2)',
            backdropFilter: 'blur(20px)',
            height: '600px',
            overflow: 'hidden'
          }}>
            <CardContent>
              <Box display="flex" alignItems="center" mb={3}>
                <Shield sx={{ color: '#00ff88', mr: 2 }} />
                <Typography variant="h5" fontWeight={700} color="#00ff88">
                  Recent Vulnerabilities
                </Typography>
              </Box>
              
              {loading ? (
                <Box>
                  <LinearProgress sx={{ mb: 2, bgcolor: 'rgba(0,255,136,0.1)' }} />
                  <Typography color="text.secondary">Loading vulnerabilities...</Typography>
                </Box>
              ) : (
                <List sx={{ maxHeight: 500, overflow: 'auto' }}>
                  {vulnerabilities.slice(0, 10).map((vuln, index) => (
                    <Fade in={true} timeout={500 + index * 100} key={vuln.id}>
                      <ListItem 
                        sx={{ 
                          border: '1px solid rgba(255,255,255,0.1)',
                          borderRadius: 2,
                          mb: 2,
                          bgcolor: 'rgba(255,255,255,0.02)',
                          transition: 'all 0.3s ease',
                          '&:hover': {
                            bgcolor: 'rgba(0,255,136,0.05)',
                            border: '1px solid rgba(0,255,136,0.3)',
                            transform: 'translateX(8px)'
                          }
                        }}
                      >
                        <Avatar sx={{ 
                          bgcolor: getSeverityColor(vuln.severity), 
                          mr: 2,
                          width: 40,
                          height: 40
                        }}>
                          {getSeverityIcon(vuln.severity)}
                        </Avatar>
                        <ListItemText
                          primary={
                            <Typography variant="subtitle1" fontWeight={600} color="text.primary">
                              {vuln.title}
                            </Typography>
                          }
                          secondary={
                            <Box>
                              <Typography variant="body2" color="text.secondary" mb={1}>
                                ID: {vuln.vulnerability_id} • CVSS: {vuln.cvss_score}
                              </Typography>
                              <Box display="flex" gap={1} flexWrap="wrap">
                                <Chip 
                                  size="small" 
                                  label={vuln.severity}
                                  sx={{ 
                                    bgcolor: getSeverityColor(vuln.severity),
                                    color: 'white',
                                    fontWeight: 600
                                  }}
                                />
                                {vuln.affected_tools.map(tool => (
                                  <Chip 
                                    key={tool}
                                    size="small" 
                                    label={tool}
                                    variant="outlined"
                                    sx={{ color: '#00ff88', borderColor: '#00ff88' }}
                                  />
                                ))}
                              </Box>
                            </Box>
                          }
                        />
                      </ListItem>
                    </Fade>
                  ))}
                </List>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* AI Tools Status */}
        <Grid item xs={12} lg={4}>
          <Card sx={{ 
            bgcolor: 'rgba(255,255,255,0.02)',
            border: '1px solid rgba(33,150,243,0.2)',
            backdropFilter: 'blur(20px)',
            height: '600px',
            overflow: 'hidden'
          }}>
            <CardContent>
              <Box display="flex" alignItems="center" mb={3}>
                <Code sx={{ color: '#2196f3', mr: 2 }} />
                <Typography variant="h5" fontWeight={700} color="#2196f3">
                  AI Tools Status
                </Typography>
              </Box>
              
              <List sx={{ maxHeight: 500, overflow: 'auto' }}>
                {tools.map((tool, index) => (
                  <Fade in={true} timeout={300 + index * 100} key={tool.id}>
                    <ListItem 
                      sx={{ 
                        border: '1px solid rgba(255,255,255,0.1)',
                        borderRadius: 2,
                        mb: 2,
                        bgcolor: 'rgba(255,255,255,0.02)',
                        transition: 'all 0.3s ease',
                        '&:hover': {
                          bgcolor: 'rgba(33,150,243,0.05)',
                          border: '1px solid rgba(33,150,243,0.3)',
                        }
                      }}
                    >
                      <ListItemText
                        primary={
                          <Typography variant="subtitle1" fontWeight={600} color="text.primary">
                            {tool.display_name}
                          </Typography>
                        }
                        secondary={
                          <Box>
                            <Typography variant="body2" color="text.secondary" mb={1}>
                              {tool.vendor}
                            </Typography>
                            <Box display="flex" gap={1}>
                              <Chip 
                                size="small" 
                                label={`${tool.total_vulnerabilities} total`}
                                variant="outlined"
                                sx={{ fontSize: '0.7rem' }}
                              />
                              {tool.critical_vulnerabilities > 0 && (
                                <Chip 
                                  size="small" 
                                  label={`${tool.critical_vulnerabilities} critical`}
                                  sx={{ 
                                    bgcolor: '#ff1744',
                                    color: 'white',
                                    fontSize: '0.7rem'
                                  }}
                                />
                              )}
                            </Box>
                          </Box>
                        }
                      />
                    </ListItem>
                  </Fade>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

    </Box>
    </Box>
  );
};

export default Dashboard;