import React from 'react';
import {
  Box,
  Container,
  Typography,
  IconButton,
  Divider,
  useMediaQuery,
  useTheme,
} from '@mui/material';
import {
  GitHub as GitHubIcon,
  LinkedIn as LinkedInIcon,
  Twitter as TwitterIcon,
} from '@mui/icons-material';

export const Footer: React.FC = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const currentYear = new Date().getFullYear();

  const socialLinks = [
    { icon: <GitHubIcon />, url: '#', label: 'GitHub' },
    { icon: <LinkedInIcon />, url: '#', label: 'LinkedIn' },
    { icon: <TwitterIcon />, url: '#', label: 'Twitter' },
  ];

  return (
    <Box
      component="footer"
      sx={{
        bgcolor: 'background.paper',
        color: 'text.primary',
        py: { xs: 4, sm: 5 },
        mt: 'auto',
        borderTop: '1px solid',
        borderColor: 'divider',
      }}
    >
      <Container maxWidth="lg">
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            textAlign: 'center',
          }}
        >
          <Typography
            variant={isMobile ? 'h6' : 'h5'}
            sx={{
              fontWeight: 700,
              mb: 2,
              background: 'linear-gradient(45deg, #42a5f5 30%, #90caf9 90%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            Document Assistance
          </Typography>
          
          <Typography
            variant="body2"
            sx={{
              mb: 3,
              color: 'text.secondary',
              lineHeight: 1.7,
              maxWidth: '600px',
            }}
          >
            Empowering you to effortlessly extract insights and information from your documents. Our AI-powered assistant is here to help you navigate, understand, and utilize your data like never before.
          </Typography>

          <Box sx={{ display: 'flex', gap: 1.5, mb: 3 }}>
            {socialLinks.map((social, index) => (
              <IconButton
                key={index}
                href={social.url}
                target="_blank"
                rel="noopener noreferrer"
                aria-label={social.label}
                sx={{
                  color: 'text.secondary',
                  bgcolor: 'grey.100',
                  '&:hover': {
                    color: 'primary.main',
                    bgcolor: 'grey.200',
                    transform: 'translateY(-2px)',
                  },
                  transition: 'all 0.3s ease',
                }}
              >
                {social.icon}
              </IconButton>
            ))}
          </Box>

          <Divider sx={{ width: '100%', my: 3, bgcolor: 'grey.300' }} />

          <Box
            sx={{
              display: 'flex',
              flexDirection: { xs: 'column', sm: 'row' },
              justifyContent: 'center',
              alignItems: 'center',
              gap: { xs: 1, sm: 2 },
            }}
          >
            <Typography
              variant="body2"
              sx={{
                color: 'text.secondary',
              }}
            >
              &copy; {currentYear} Document Assistance. All rights reserved.
            </Typography>
          </Box>
        </Box>
      </Container>
    </Box>
  );
};

export default Footer;
