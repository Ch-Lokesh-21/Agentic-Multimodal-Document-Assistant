import React, { useEffect, useRef } from 'react';
import { Box, Typography, IconButton, Paper, alpha, Fade } from '@mui/material';
import { Menu as MenuIcon, Chat as ChatIcon } from '@mui/icons-material';
import { useMessages } from '../hooks/index.ts';
import MessageList from './MessageList.tsx';
import MessageInput from './MessageInput.tsx';

interface ChatAreaProps {
  sessionId?: string;
  onMenuClick?: () => void;
}

export const ChatArea: React.FC<ChatAreaProps> = ({ sessionId, onMenuClick }) => {
  const { data: messages, isLoading } = useMessages(sessionId);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  if (!sessionId) {
    return (
      <Box
        sx={{
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          p: 3,
          bgcolor: alpha('#000', 0.01),
        }}
      >
        <Fade in timeout={500}>
          <Paper
            elevation={0}
            sx={{
              p: 6,
              borderRadius: 4,
              textAlign: 'center',
              maxWidth: 500,
              bgcolor: 'background.paper',
              boxShadow: '0 4px 20px rgba(0,0,0,0.06)',
            }}
          >
            <Box
              sx={{
                width: 80,
                height: 80,
                borderRadius: '50%',
                bgcolor: alpha('#1976d2', 0.08),
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                mx: 'auto',
                mb: 3,
              }}
            >
              <ChatIcon sx={{ fontSize: 40, color: 'primary.main' }} />
            </Box>
            <Typography variant="h5" fontWeight={700} gutterBottom color="text.primary">
              Welcome to Document Assistance
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mt: 2, lineHeight: 1.7 }}>
              Select a session from the sidebar or create a new one to start asking questions about your documents
            </Typography>
          </Paper>
        </Fade>
      </Box>
    );
  }

  return (
    <Box
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        bgcolor: alpha('#000', 0.01),
      }}
    >
      {onMenuClick && (
        <Paper
          elevation={0}
          sx={{
            px: 2,
            py: 1.5,
            borderBottom: '1px solid',
            borderColor: 'divider',
            bgcolor: 'background.paper',
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <IconButton
              edge="start"
              onClick={onMenuClick}
              sx={{
                mr: 1,
                '&:hover': {
                  bgcolor: alpha('#000', 0.08),
                },
              }}
            >
              <MenuIcon />
            </IconButton>
            <Typography variant="h6" fontWeight={600}>
              Chat
            </Typography>
          </Box>
        </Paper>
      )}

      <Box
        sx={{
          flexGrow: 1,
          overflow: 'auto',
          px: 3,
          py: 2,
        }}
      >
        <Box sx={{ maxWidth: 1200, mx: 'auto' }}>
          <MessageList messages={messages || []} isLoading={isLoading} />
          <div ref={messagesEndRef} />
        </Box>
      </Box>

      <MessageInput sessionId={sessionId} />
    </Box>
  );
};

export default ChatArea;
