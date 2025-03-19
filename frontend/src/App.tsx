import React, { useState, useEffect } from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { Box, CssBaseline, CircularProgress, Typography, Container, Paper } from '@mui/material';
import ChatInterface from './components/ChatInterface';
import Login from './components/Auth/Login';
import Register from './components/Auth/Register';
import PatientInfoForm from './components/PatientInfoForm';
import { Message, ChatResponse, ChatRequest, PatientInfo, AuthState, LoginResponse, RegisterResponse } from './types';

// Create theme with NHS color palette
const theme = createTheme({
  palette: {
    mode: 'dark',
    background: {
      default: '#121212',
      paper: '#1e1e1e',
    },
    primary: {
      main: '#0072CE', // NHS Blue
      light: '#41B6E6', // NHS Light Blue
      dark: '#003087', // NHS Dark Blue
    },
    secondary: {
      main: '#00A499', // NHS Green
      light: '#41B6AD',
      dark: '#006747',
    },
    error: {
      main: '#DA291C', // NHS Red
    },
    warning: {
      main: '#FFB81C', // NHS Yellow
    },
    info: {
      main: '#330072', // NHS Purple
    },
    success: {
      main: '#009639', // NHS Green
    },
    text: {
      primary: '#FFFFFF',
      secondary: 'rgba(255, 255, 255, 0.7)',
    },
  },
  typography: {
    fontFamily: "'Segoe UI', 'Roboto', 'Helvetica', 'Arial', sans-serif",
    h1: {
      fontWeight: 700,
    },
    h2: {
      fontWeight: 700,
    },
    h3: {
      fontWeight: 600,
    },
    h4: {
      fontWeight: 600,
    },
    h5: {
      fontWeight: 500,
    },
    h6: {
      fontWeight: 500,
    },
    subtitle1: {
      fontWeight: 500,
    },
    button: {
      textTransform: 'none',
      fontWeight: 500,
    },
  },
  shape: {
    borderRadius: 8,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          padding: '8px 16px',
          transition: 'all 0.2s ease-in-out',
        },
        contained: {
          boxShadow: '0 3px 5px 2px rgba(0, 114, 206, .2)',
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            '& fieldset': {
              borderColor: 'rgba(255, 255, 255, 0.23)',
            },
            '&:hover fieldset': {
              borderColor: '#0072CE',
            },
            '&.Mui-focused fieldset': {
              borderColor: '#0072CE',
            },
          },
        },
      },
    },
  },
});

// Make sure there's no reference to darkTheme anywhere
const appTheme = theme;

// Auth views enum
enum AppView {
  LOGIN,
  REGISTER,
  PATIENT_INFO,
  CHAT,
  LOADING,
}

const App: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentView, setCurrentView] = useState<AppView>(AppView.LOADING);
  const [auth, setAuth] = useState<AuthState>({
    isAuthenticated: false,
    token: null,
    user_id: null,
    patientInfo: null,
  });

  // Check for existing auth on initial load
  useEffect(() => {
    const token = localStorage.getItem('auth_token');
    const user_id = localStorage.getItem('user_id');
    
    if (token && user_id) {
      setAuth({
        isAuthenticated: true,
        token,
        user_id,
        patientInfo: null,
      });
      
      // Check if we need to get patient info
      fetchPatientInfo(token, user_id);
    } else {
      setCurrentView(AppView.LOGIN);
    }
  }, []);

  const fetchPatientInfo = async (token: string, user_id: string) => {
    try {
      const response = await fetch(`http://localhost:8000/context/${user_id}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.patient_info) {
          setAuth(prevAuth => ({
            ...prevAuth,
            patientInfo: data.patient_info
          }));
          setCurrentView(AppView.CHAT);
        } else {
          setCurrentView(AppView.PATIENT_INFO);
        }
      } else {
        setCurrentView(AppView.PATIENT_INFO);
      }
    } catch (error) {
      console.error('Error fetching patient info:', error);
      setCurrentView(AppView.PATIENT_INFO);
    }
  };

  const handleLoginSuccess = (data: LoginResponse) => {
    // Store token in localStorage
    localStorage.setItem('auth_token', data.access_token);
    localStorage.setItem('user_id', data.user_id);
    
    setAuth({
      isAuthenticated: true,
      token: data.access_token,
      user_id: data.user_id,
      patientInfo: null,
    });
    
    // Switch to patient info view
    setCurrentView(AppView.PATIENT_INFO);
  };

  const handleRegisterSuccess = (data: RegisterResponse) => {
    // After registration, show login view
    setCurrentView(AppView.LOGIN);
  };

  const handlePatientInfoComplete = (patientInfo: PatientInfo) => {
    setAuth(prevAuth => ({
      ...prevAuth,
      patientInfo
    }));
    
    // Show a welcome message
    const welcomeMessage: Message = {
      type: 'assistant',
      content: `Welcome to the NHS Digital Front Desk. How can I help you today?`,
    };
    
    setMessages([welcomeMessage]);
    setCurrentView(AppView.CHAT);
  };

  const handleLogout = () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_id');
    
    setAuth({
      isAuthenticated: false,
      token: null,
      user_id: null,
      patientInfo: null,
    });
    
    setMessages([]);
    setCurrentView(AppView.LOGIN);
  };

  const handleSendMessage = async (message: string): Promise<void> => {
    if (!auth.isAuthenticated || !auth.token || !auth.user_id) {
      console.error('User not authenticated');
      return;
    }

    // Add user message to chat
    const userMessage: Message = {
      type: 'user',
      content: message,
    };
    setMessages(prev => [...prev, userMessage]);

    try {
      const chatRequest: ChatRequest = {
        channel_type: 'web_portal',
        message: message,
        user_id: auth.user_id,
        patient_info: auth.patientInfo || undefined,
      };

      const response = await fetch('http://localhost:8000/inquiries', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${auth.token}`
        },
        body: JSON.stringify(chatRequest),
      });

      const data: ChatResponse = await response.json();
      
      // Add assistant response to chat with additional information
      const assistantMessage: Message = {
        type: 'assistant',
        content: data.response,
        suggestedActions: data.suggested_actions,
        triageResult: {
          urgencyLevel: data.triage_result.urgency_level,
          recommendedAction: data.triage_result.recommended_action,
          requiresHumanAttention: data.triage_result.requires_human_attention,
        },
      };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      // Show error message to user
      const errorMessage: Message = {
        type: 'assistant',
        content: 'Sorry, there was a problem processing your request. Please try again.',
      };
      setMessages(prev => [...prev, errorMessage]);
    }
  };

  // Render appropriate view based on state
  const renderCurrentView = () => {
    switch (currentView) {
      case AppView.LOADING:
        return (
          <Container sx={{ 
            display: 'flex', 
            justifyContent: 'center', 
            alignItems: 'center', 
            height: '100vh',
            flexDirection: 'column',
            gap: 2, 
          }}>
            <CircularProgress size={60} thickness={4} color="primary" />
            <Typography variant="h6" color="text.secondary">Loading NHS Digital Front Desk...</Typography>
          </Container>
        );
      case AppView.LOGIN:
        return (
          <Login 
            onLoginSuccess={handleLoginSuccess} 
            onRegisterClick={() => setCurrentView(AppView.REGISTER)} 
          />
        );
      case AppView.REGISTER:
        return (
          <Register 
            onRegisterSuccess={handleRegisterSuccess} 
            onLoginClick={() => setCurrentView(AppView.LOGIN)} 
          />
        );
      case AppView.PATIENT_INFO:
        return (
          <PatientInfoForm 
            userId={auth.user_id!}
            token={auth.token!}
            onComplete={handlePatientInfoComplete}
            initialData={auth.patientInfo || undefined}
          />
        );
      case AppView.CHAT:
        return (
          <ChatInterface 
            messages={messages} 
            onSendMessage={handleSendMessage} 
            onLogout={handleLogout}
            patientInfo={auth.patientInfo}
          />
        );
      default:
        return (
          <Box sx={{ 
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            height: '100vh',
            gap: 2,
            p: 3,
            textAlign: 'center',
          }}>
            <Typography variant="h5" color="error">Something went wrong</Typography>
            <Typography variant="body1" color="text.secondary">Please refresh the page to try again.</Typography>
            <Paper 
              sx={{ 
                p: 2, 
                maxWidth: 400, 
                bgcolor: 'background.paper',
                borderLeft: '4px solid #DA291C', // NHS Red
              }}
            >
              <Typography variant="body2" color="text.secondary">
                If the problem persists, please contact NHS Digital support.
              </Typography>
            </Paper>
          </Box>
        );
    }
  };

  return (
    <ThemeProvider theme={appTheme}>
      <CssBaseline />
      <Box
        sx={{
          height: '100vh',
          display: 'flex',
          flexDirection: 'column',
          bgcolor: 'background.default',
          backgroundImage: appTheme.palette.mode === 'dark' 
            ? 'radial-gradient(circle at 25% 50%, rgba(0, 114, 206, 0.1) 0%, transparent 50%), radial-gradient(circle at 75% 25%, rgba(0, 164, 153, 0.1) 0%, transparent 50%)'
            : 'none',
        }}
      >
        {renderCurrentView()}
      </Box>
    </ThemeProvider>
  );
};

export default App; 