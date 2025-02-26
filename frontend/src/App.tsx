import React, { useState } from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { Box, CssBaseline } from '@mui/material';
import ChatInterface from './components/ChatInterface';
import { Message, ChatResponse, ChatRequest } from './types';

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    background: {
      default: '#202123',
      paper: '#343541',
    },
    primary: {
      main: '#10a37f',
    },
  },
});

const App: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);

  const handleSendMessage = async (message: string): Promise<void> => {
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
        user_id: 'web_user_1',
      };

      const response = await fetch('http://localhost:8000/inquiries', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
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
    }
  };

  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <Box
        sx={{
          height: '100vh',
          display: 'flex',
          flexDirection: 'column',
          bgcolor: 'background.default',
        }}
      >
        <ChatInterface messages={messages} onSendMessage={handleSendMessage} />
      </Box>
    </ThemeProvider>
  );
};

export default App; 