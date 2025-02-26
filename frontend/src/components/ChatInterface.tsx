import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  TextField,
  IconButton,
  Paper,
  Typography,
  Container,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import MicIcon from '@mui/icons-material/Mic';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import WarningIcon from '@mui/icons-material/Warning';
import { Message } from '../types';

interface ChatInterfaceProps {
  messages: Message[];
  onSendMessage: (message: string) => void;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ messages, onSendMessage }) => {
  const [input, setInput] = useState<string>('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = (): void => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = (e: React.FormEvent): void => {
    e.preventDefault();
    if (input.trim()) {
      onSendMessage(input);
      setInput('');
    }
  };

  const getUrgencyColor = (level: string): string => {
    switch (level?.toUpperCase()) {
      case 'HIGH':
        return '#ff4444';
      case 'MEDIUM':
        return '#ffbb33';
      case 'LOW':
        return '#00C851';
      default:
        return '#33b5e5';
    }
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Messages Container */}
      <Box
        sx={{
          flex: 1,
          overflow: 'auto',
          p: 2,
          display: 'flex',
          flexDirection: 'column',
          gap: 2,
        }}
      >
        {messages.length === 0 ? (
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              height: '100%',
            }}
          >
            <Typography variant="h4" color="text.secondary">
              What can I help with?
            </Typography>
          </Box>
        ) : (
          messages.map((message, index) => (
            <Paper
              key={index}
              elevation={0}
              sx={{
                p: 2,
                bgcolor: message.type === 'user' ? 'background.paper' : 'background.default',
                maxWidth: '80%',
                alignSelf: message.type === 'user' ? 'flex-end' : 'flex-start',
              }}
            >
              <Typography>{message.content}</Typography>
              
              {message.type === 'assistant' && message.triageResult && (
                <Box sx={{ mt: 2 }}>
                  <Chip
                    icon={<WarningIcon />}
                    label={`Urgency: ${message.triageResult.urgencyLevel}`}
                    sx={{
                      bgcolor: getUrgencyColor(message.triageResult.urgencyLevel),
                      color: 'white',
                      mb: 1,
                    }}
                  />
                  <Typography variant="body2" color="text.secondary">
                    {message.triageResult.recommendedAction}
                  </Typography>
                </Box>
              )}

              {message.type === 'assistant' && message.suggestedActions && message.suggestedActions.length > 0 && (
                <List dense sx={{ mt: 1 }}>
                  {message.suggestedActions.map((action, actionIndex) => (
                    <ListItem key={actionIndex} sx={{ p: 0 }}>
                      <ListItemIcon sx={{ minWidth: 36 }}>
                        <ArrowForwardIcon color="primary" fontSize="small" />
                      </ListItemIcon>
                      <ListItemText
                        primary={action}
                        sx={{
                          '& .MuiListItemText-primary': {
                            fontSize: '0.9rem',
                            color: 'text.secondary',
                          },
                        }}
                      />
                    </ListItem>
                  ))}
                </List>
              )}
            </Paper>
          ))
        )}
        <div ref={messagesEndRef} />
      </Box>

      {/* Input Container */}
      <Container maxWidth="md" sx={{ p: 2 }}>
        <Paper
          component="form"
          onSubmit={handleSubmit}
          sx={{
            p: '2px 4px',
            display: 'flex',
            alignItems: 'center',
            borderRadius: 2,
          }}
        >
          <TextField
            fullWidth
            value={input}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setInput(e.target.value)}
            placeholder="Ask anything"
            variant="standard"
            sx={{ ml: 1, flex: 1 }}
            InputProps={{ disableUnderline: true }}
          />
          <IconButton color="primary" sx={{ p: '10px' }}>
            <MicIcon />
          </IconButton>
          <Divider sx={{ height: 28, m: 0.5 }} orientation="vertical" />
          <IconButton
            color="primary"
            sx={{ p: '10px' }}
            onClick={handleSubmit}
            type="submit"
          >
            <SendIcon />
          </IconButton>
        </Paper>
      </Container>
    </Box>
  );
};

export default ChatInterface; 