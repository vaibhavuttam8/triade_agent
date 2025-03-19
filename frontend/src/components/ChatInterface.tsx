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
  AppBar,
  Toolbar,
  Button,
  Avatar,
  useMediaQuery,
  useTheme,
  Card,
  CardContent,
  Grid,
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import MicIcon from '@mui/icons-material/Mic';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import WarningIcon from '@mui/icons-material/Warning';
import ExitToAppIcon from '@mui/icons-material/ExitToApp';
import AccountCircleIcon from '@mui/icons-material/AccountCircle';
import HealthAndSafetyIcon from '@mui/icons-material/HealthAndSafety';
import TextsmsIcon from '@mui/icons-material/Textsms';
import ReactMarkdown from 'react-markdown';
import { Message, PatientInfo } from '../types';

interface ChatInterfaceProps {
  messages: Message[];
  onSendMessage: (message: string) => void;
  onLogout: () => void;
  patientInfo: PatientInfo | null;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ 
  messages, 
  onSendMessage, 
  onLogout,
  patientInfo
}) => {
  const [input, setInput] = useState<string>('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

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
      case 'CRITICAL':
        return '#CC0000';
      default:
        return '#33b5e5';
    }
  };

  const formatMessageContent = (content: string) => {
    // Replace numbered list patterns like "1. ", "2. " with markdown syntax
    let formattedContent = content.replace(/(\d+)\.\s/g, '$1\\. ');
    
    // Check if the content contains a questionnaire pattern
    if (formattedContent.includes("Please answer the following questions") || 
        formattedContent.includes("answer these questions") ||
        formattedContent.includes("the following")) {
      
      // Split by numbers at the beginning of lines
      const parts = formattedContent.split(/(?=\d+\\\.)/);
      
      if (parts.length > 1) {
        // First part contains introduction
        let result = parts[0].trim();
        
        // Add a divider after the introduction
        result += "\n\n---\n\n";
        
        // Process each question
        for (let i = 1; i < parts.length; i++) {
          const question = parts[i];
          // Replace the escaped number format with bold formatting and add a visual indicator
          const formattedQuestion = question.replace(/(\d+)\\\.\s*/, "**Question $1:** ");
          // Add proper spacing between questions
          result += formattedQuestion.trim() + "\n\n";
        }
        
        return result;
      }
    }
    
    // For other numbered lists, add some formatting
    return formattedContent.replace(/(\d+)\\\.\s+([^\n]+)/g, "**$1.** $2");
  };

  return (
    <Box sx={{ 
      height: '100%', 
      display: 'flex', 
      flexDirection: 'column',
      bgcolor: theme.palette.mode === 'dark' ? '#121212' : '#f5f5f5',
    }}>
      {/* Header */}
      <AppBar 
        position="static" 
        elevation={0}
        sx={{ 
          bgcolor: theme.palette.mode === 'dark' ? '#1e1e1e' : '#0072CE', // NHS Blue for light mode
          borderBottom: `1px solid ${theme.palette.divider}`,
        }}
      >
        <Toolbar>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <HealthAndSafetyIcon sx={{ mr: 1 }} />
            <Typography 
              variant="h6" 
              component="div" 
              sx={{ 
                flexGrow: 1,
                fontWeight: 'bold',
                letterSpacing: '0.5px',
              }}
            >
              NHS Digital Front Desk
            </Typography>
          </Box>
          <Box sx={{ flexGrow: 1 }} />
          {patientInfo && (
            <Box 
              sx={{ 
                display: 'flex', 
                alignItems: 'center', 
                mr: 2,
                borderRadius: 1,
                bgcolor: 'rgba(255, 255, 255, 0.1)',
                p: 0.75,
                px: 1.5,
              }}
            >
              <Avatar 
                sx={{ 
                  mr: 1, 
                  bgcolor: theme.palette.primary.dark,
                  boxShadow: 1,
                }}
              >
                {patientInfo.sex ? patientInfo.sex.charAt(0).toUpperCase() : <AccountCircleIcon />}
              </Avatar>
              <Box>
                <Typography variant="subtitle2" sx={{ fontWeight: 'medium' }}>
                  {patientInfo.age ? `Age: ${patientInfo.age}` : 'Patient'}
                </Typography>
                {patientInfo.allergies && patientInfo.allergies.length > 0 && (
                  <Chip
                    label={`${patientInfo.allergies.length} allergies`}
                    size="small"
                    color="error"
                    sx={{ 
                      height: 20, 
                      fontSize: '0.7rem', 
                      mr: 1,
                      fontWeight: 'bold',
                    }}
                  />
                )}
              </Box>
            </Box>
          )}
          <Button 
            color="inherit" 
            onClick={onLogout}
            startIcon={<ExitToAppIcon />}
            variant="outlined"
            size={isMobile ? "small" : "medium"}
            sx={{ 
              borderRadius: 2,
              textTransform: 'none',
              borderColor: 'rgba(255, 255, 255, 0.3)',
              '&:hover': {
                borderColor: 'rgba(255, 255, 255, 0.6)',
                bgcolor: 'rgba(255, 255, 255, 0.1)',
              }
            }}
          >
            {isMobile ? '' : 'Logout'}
          </Button>
        </Toolbar>
      </AppBar>

      {/* Messages Container */}
      <Box
        sx={{
          flex: 1,
          overflow: 'auto',
          p: { xs: 1, sm: 2, md: 3 },
          display: 'flex',
          flexDirection: 'column',
          gap: 2,
          backgroundImage: theme.palette.mode === 'dark' 
            ? 'linear-gradient(rgba(0, 0, 0, 0.2) 1px, transparent 1px), linear-gradient(90deg, rgba(0, 0, 0, 0.2) 1px, transparent 1px)'
            : 'linear-gradient(rgba(0, 0, 0, 0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(0, 0, 0, 0.05) 1px, transparent 1px)',
          backgroundSize: '20px 20px',
        }}
      >
        {messages.length === 0 ? (
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              height: '100%',
              flexDirection: 'column',
            }}
          >
            <Card 
              elevation={0} 
              sx={{ 
                bgcolor: 'background.paper',
                maxWidth: 600,
                borderRadius: 3,
                boxShadow: 3,
                opacity: 0.9,
                p: 3,
                textAlign: 'center',
              }}
            >
              <CardContent>
                <HealthAndSafetyIcon 
                  color="primary" 
                  sx={{ 
                    fontSize: 60, 
                    mb: 2,
                    opacity: 0.7,
                  }} 
                />
                <Typography variant="h5" color="primary" gutterBottom fontWeight="bold">
                  Welcome to NHS Digital Front Desk
                </Typography>
                <Typography variant="body1" color="text.secondary" paragraph>
                  You can describe your symptoms or ask health-related questions. 
                  Our AI will provide guidance and triage your case.
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Type your message below to get started.
                </Typography>
              </CardContent>
            </Card>
          </Box>
        ) : (
          messages.map((message, index) => (
            <Card
              key={index}
              elevation={0}
              sx={{
                maxWidth: '85%',
                width: 'auto',
                alignSelf: message.type === 'user' ? 'flex-end' : 'flex-start',
                borderRadius: message.type === 'user' ? '18px 18px 0 18px' : '18px 18px 18px 0',
                bgcolor: message.type === 'user' 
                  ? theme.palette.primary.main 
                  : theme.palette.mode === 'dark' ? 'background.paper' : 'white',
                boxShadow: 3,
                position: 'relative',
                overflow: 'visible',
                '&::before': message.type === 'assistant' ? {
                  content: '""',
                  position: 'absolute',
                  width: '10px',
                  height: '10px',
                  bgcolor: theme.palette.mode === 'dark' ? 'background.paper' : 'white',
                  left: '-5px',
                  bottom: '10px',
                  transform: 'rotate(45deg)',
                  boxShadow: '-2px 2px 2px rgba(0, 0, 0, 0.1)',
                } : {},
              }}
            >
              <CardContent sx={{ p: { xs: 1.5, sm: 2 } }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <Avatar 
                    sx={{ 
                      width: 28, 
                      height: 28, 
                      mr: 1, 
                      bgcolor: message.type === 'user' 
                        ? theme.palette.primary.dark 
                        : theme.palette.secondary.main
                    }}
                  >
                    {message.type === 'user' 
                      ? <AccountCircleIcon fontSize="small" /> 
                      : <HealthAndSafetyIcon fontSize="small" />}
                  </Avatar>
                  <Typography 
                    variant="caption" 
                    sx={{ 
                      opacity: 0.7,
                      fontWeight: 'medium',
                      color: message.type === 'user' ? 'white' : 'text.primary',
                    }}
                  >
                    {message.type === 'user' ? 'You' : 'NHS Assistant'}
                  </Typography>
                </Box>
                
                <Typography 
                  sx={{ 
                    color: message.type === 'user' ? 'white' : 'text.primary',
                    '& ul, & ol': {
                      pl: 2,
                      mb: 1,
                    },
                    '& li': {
                      mb: 0.5,
                    },
                    '& p': {
                      lineHeight: 1.6,
                    },
                    '& strong': {
                      display: 'inline-block',
                      mb: 0.5,
                      mt: 1,
                    },
                    '& p + p': {
                      mt: 2,
                    },
                  }}
                >
                  {message.type === 'user' ? (
                    message.content
                  ) : (
                    <ReactMarkdown components={{
                      p: ({node, ...props}) => <Typography component="div" variant="body1" sx={{ mb: 1 }} {...props} />,
                      li: ({node, ...props}) => (
                        <Box component="li" sx={{ mb: 1, display: 'flex', alignItems: 'flex-start' }} {...props} />
                      ),
                      strong: ({node, ...props}) => (
                        <Typography 
                          component="span" 
                          sx={{ 
                            fontWeight: 'bold', 
                            color: theme.palette.primary.main,
                            fontSize: '1.05rem'
                          }} 
                          {...props} 
                        />
                      ),
                      hr: () => (
                        <Divider 
                          sx={{ 
                            my: 2,
                            borderColor: theme.palette.primary.light,
                            opacity: 0.7,
                            width: '100%',
                          }} 
                        />
                      ),
                    }}>
                      {formatMessageContent(message.content)}
                    </ReactMarkdown>
                  )}
                </Typography>
                
                {message.type === 'assistant' && message.triageResult && (
                  <Box 
                    sx={{ 
                      mt: 2, 
                      p: 1.5, 
                      borderRadius: 2,
                      bgcolor: theme.palette.mode === 'dark' 
                        ? 'rgba(0, 0, 0, 0.2)' 
                        : 'rgba(0, 0, 0, 0.03)',
                      border: `1px solid ${theme.palette.divider}`,
                    }}
                  >
                    <Chip
                      icon={<WarningIcon />}
                      label={`Urgency: ${message.triageResult.urgencyLevel}`}
                      sx={{
                        bgcolor: getUrgencyColor(message.triageResult.urgencyLevel),
                        color: 'white',
                        mb: 1,
                        fontWeight: 'bold',
                        px: 1,
                      }}
                    />
                    <Typography 
                      variant="body2" 
                      sx={{ 
                        color: theme.palette.mode === 'dark' 
                          ? 'rgba(255, 255, 255, 0.7)' 
                          : 'rgba(0, 0, 0, 0.7)',
                        fontStyle: 'italic',
                      }}
                    >
                      {message.triageResult.recommendedAction}
                    </Typography>
                  </Box>
                )}

                {message.type === 'assistant' && message.suggestedActions && message.suggestedActions.length > 0 && (
                  <Box 
                    sx={{ 
                      mt: 2,
                      p: 1.5,
                      borderRadius: 2,
                      bgcolor: theme.palette.mode === 'dark' 
                        ? 'rgba(0, 0, 0, 0.2)' 
                        : 'rgba(240, 240, 240, 0.6)',
                      border: `1px solid ${theme.palette.divider}`,
                    }}
                  >
                    <Typography 
                      variant="subtitle2" 
                      sx={{ 
                        mb: 1, 
                        color: theme.palette.primary.main,
                        fontWeight: 'medium',
                      }}
                    >
                      Suggested Actions:
                    </Typography>
                    <List dense disablePadding>
                      {message.suggestedActions.map((action, actionIndex) => (
                        <ListItem 
                          key={actionIndex} 
                          sx={{ 
                            p: 0.5,
                            borderRadius: 1,
                            '&:hover': {
                              bgcolor: theme.palette.action.hover,
                            },
                          }}
                        >
                          <ListItemIcon sx={{ minWidth: 36 }}>
                            <ArrowForwardIcon color="primary" fontSize="small" />
                          </ListItemIcon>
                          <ListItemText
                            primary={action}
                            sx={{
                              '& .MuiListItemText-primary': {
                                fontSize: '0.9rem',
                                color: theme.palette.text.secondary,
                                fontWeight: 'medium',
                              },
                            }}
                          />
                        </ListItem>
                      ))}
                    </List>
                  </Box>
                )}
              </CardContent>
            </Card>
          ))
        )}
        <div ref={messagesEndRef} />
      </Box>

      {/* Input Container */}
      <Container 
        maxWidth="md" 
        sx={{ 
          p: { xs: 1, sm: 2 },
          bgcolor: theme.palette.mode === 'dark' ? '#1e1e1e' : '#f0f0f0',
          borderTop: `1px solid ${theme.palette.divider}`,
        }}
      >
        <Paper
          component="form"
          onSubmit={handleSubmit}
          sx={{
            p: '2px 4px',
            display: 'flex',
            alignItems: 'center',
            borderRadius: 3,
            boxShadow: 3,
            bgcolor: theme.palette.background.paper,
            position: 'relative',
            '&:before': {
              content: '""',
              position: 'absolute',
              top: -1,
              left: -1,
              right: -1,
              bottom: -1,
              borderRadius: 'inherit',
              background: 'linear-gradient(45deg, #0072CE, #41B6E6)', // NHS Blue gradient
              opacity: 0.3,
              zIndex: -1,
            },
          }}
        >
          <TextField
            fullWidth
            value={input}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setInput(e.target.value)}
            placeholder="Describe your symptoms or ask a question"
            variant="standard"
            sx={{ 
              ml: 1, 
              flex: 1,
              '& .MuiInputBase-root': {
                fontSize: '1rem',
                p: 0.5,
              },
            }}
            InputProps={{ 
              disableUnderline: true,
              startAdornment: (
                <TextsmsIcon 
                  sx={{ 
                    mr: 1, 
                    color: theme.palette.text.secondary,
                    opacity: 0.7,
                  }} 
                />
              ),
            }}
          />
          <IconButton 
            color="primary" 
            sx={{ 
              p: '12px',
              '&:hover': {
                bgcolor: theme.palette.primary.main,
                color: 'white',
              },
              transition: 'all 0.2s',
            }}
          >
            <MicIcon />
          </IconButton>
          <Divider sx={{ height: 28, m: 0.5 }} orientation="vertical" />
          <IconButton
            color="primary"
            sx={{ 
              p: '12px',
              bgcolor: theme.palette.primary.main,
              color: 'white',
              '&:hover': {
                bgcolor: theme.palette.primary.dark,
              },
              transition: 'all 0.2s',
            }}
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