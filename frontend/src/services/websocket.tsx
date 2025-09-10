import React, { createContext, useContext, useEffect, useState, useCallback, ReactNode } from 'react';
import toast from 'react-hot-toast';
import { WebSocketMessage, Vulnerability, Alert } from '../types';

interface WebSocketContextType {
  socket: WebSocket | null;
  isConnected: boolean;
  vulnerabilityUpdates: Vulnerability[];
  alertNotifications: Alert[];
  clearVulnerabilityUpdates: () => void;
  clearAlertNotifications: () => void;
  subscribeToVulnerabilities: (filters?: any) => void;
}

const WebSocketContext = createContext<WebSocketContextType | null>(null);

export const useWebSocket = () => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  return context;
};

interface WebSocketProviderProps {
  children: ReactNode;
}

export const WebSocketProvider: React.FC<WebSocketProviderProps> = ({ children }) => {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [vulnerabilityUpdates, setVulnerabilityUpdates] = useState<Vulnerability[]>([]);
  const [alertNotifications, setAlertNotifications] = useState<Alert[]>([]);

  // Initialize WebSocket connection
  useEffect(() => {
    // For now, simulate connection without actual WebSocket
    // This will be replaced with real WebSocket when backend is running
    const simulateConnection = () => {
      console.log('Simulating WebSocket connection...');
      setIsConnected(true);
      
      // Simulate some demo updates
      setTimeout(() => {
        const demoVuln: Vulnerability = {
          id: 'demo-001',
          vulnerability_id: 'demo-001',
          title: 'Demo Critical AI Code Vulnerability',
          description: 'This is a demo vulnerability for testing the dashboard',
          severity: 'CRITICAL',
          cvss_score: 9.8,
          attack_vectors: ['rce'],
          patch_status: 'unpatched',
          poc_available: false,
          exploit_in_wild: false,
          tags: ['demo', 'critical'],
          references: [],
          affected_tools: ['cursor', 'copilot'],
          kirin_remediation_available: true,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        };
        
        setVulnerabilityUpdates(prev => [demoVuln, ...prev.slice(0, 49)]);
        toast.success('Demo vulnerability loaded');
      }, 2000);
    };

    // Try to connect to actual WebSocket, fallback to simulation
    try {
      const wsUrl = process.env.NODE_ENV === 'production' 
        ? `wss://${window.location.host}/api/ws/vulnerabilities`
        : 'ws://localhost:8080/api/ws/vulnerabilities';
      
      const newSocket = new WebSocket(wsUrl);
      
      newSocket.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setSocket(newSocket);
        toast.success('Connected to real-time updates');
      };

      newSocket.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        setSocket(null);
        // Fallback to simulation in development
        if (process.env.NODE_ENV === 'development') {
          simulateConnection();
        }
      };

      newSocket.onerror = (error) => {
        console.log('WebSocket error:', error);
        // Fallback to simulation
        simulateConnection();
      };

      newSocket.onmessage = (event) => {
        try {
          const data: WebSocketMessage = JSON.parse(event.data);
          console.log('WebSocket message received:', data);
          
          if (data.type === 'vulnerability_update' && data.data) {
            setVulnerabilityUpdates(prev => [data.data, ...prev.slice(0, 49)]);
            
            if (data.data.severity === 'CRITICAL') {
              toast.error(`Critical vulnerability: ${data.data.title}`, {
                duration: 6000,
              });
            }
          }
          
          if (data.type === 'alert_notification' && data.data) {
            setAlertNotifications(prev => [data.data, ...prev.slice(0, 49)]);
            
            if (data.data.priority === 'critical' || data.data.priority === 'high') {
              toast.error(`${data.data.priority.toUpperCase()}: ${data.data.title}`, {
                duration: 5000,
              });
            }
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      // Cleanup function
      return () => {
        if (newSocket.readyState === WebSocket.OPEN) {
          newSocket.close();
        }
      };
      
    } catch (error) {
      console.log('WebSocket connection failed, using simulation:', error);
      simulateConnection();
    }
  }, []);

  // Send heartbeat every 30 seconds
  useEffect(() => {
    if (socket && isConnected) {
      const interval = setInterval(() => {
        if (socket.readyState === WebSocket.OPEN) {
          socket.send(JSON.stringify({
            type: 'ping',
            timestamp: new Date().toISOString()
          }));
        }
      }, 30000);

      return () => clearInterval(interval);
    }
  }, [socket, isConnected]);

  const clearVulnerabilityUpdates = useCallback(() => {
    setVulnerabilityUpdates([]);
  }, []);

  const clearAlertNotifications = useCallback(() => {
    setAlertNotifications([]);
  }, []);

  const subscribeToVulnerabilities = useCallback((filters?: any) => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({
        type: 'subscribe',
        filters: filters || {}
      }));
    }
  }, [socket]);

  const value: WebSocketContextType = {
    socket,
    isConnected,
    vulnerabilityUpdates,
    alertNotifications,
    clearVulnerabilityUpdates,
    clearAlertNotifications,
    subscribeToVulnerabilities,
  };

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
};