import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Container,
  Typography,
  Button,
  Card,
  CardContent,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import {
  AutoAwesome as AIIcon,
  Speed as SpeedIcon,
  Security as SecurityIcon,
  Chat as ChatIcon,
  Description as DocumentIcon,
  TrendingUp as TrendingIcon,
} from '@mui/icons-material';
import { useAppSelector } from '../../hooks/index';
import { selectIsAuthenticated } from '../../features/auth/slices/authSlice';

export const Hero: React.FC = () => {
  const navigate = useNavigate();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.down('md'));
  const isAuthenticated = useAppSelector(selectIsAuthenticated);

  const handleGetStarted = () => {
    if (isAuthenticated) {
      navigate('/chat');
    } else {
      navigate('/register');
    }
  };

  const features = [
    {
      icon: <AIIcon sx={{ fontSize: 40 }} />,
      title: 'AI-Powered Analysis',
      description: 'Leverage advanced AI to analyze and understand your documents instantly.',
    },
    {
      icon: <SpeedIcon sx={{ fontSize: 40 }} />,
      title: 'Fast & Efficient',
      description: 'Get instant answers to your research questions without reading entire papers.',
    },
    {
      icon: <SecurityIcon sx={{ fontSize: 40 }} />,
      title: 'Secure & Private',
      description: 'Your research data is encrypted and secure. We respect your privacy.',
    },
    {
      icon: <ChatIcon sx={{ fontSize: 40 }} />,
      title: 'Interactive Chat',
      description: 'Have natural conversations about your documents with our AI assistant.',
    },
    {
      icon: <DocumentIcon sx={{ fontSize: 40 }} />,
      title: 'Document Management',
      description: 'Upload, organize, and manage all your research documents in one place.',
    },
    {
      icon: <TrendingIcon sx={{ fontSize: 40 }} />,
      title: 'Smart Citations',
      description: 'Get accurate citations and references for your research work.',
    },
  ];

  return (
    <Box
      sx={{
        minHeight: '100vh',
        bgcolor: 'background.default',
        pt: { xs: 10, sm: 12, md: 14 },
        pb: { xs: 6, sm: 8, md: 10 },
      }}
    >
      <Container maxWidth="lg">
        <Box
          sx={{
            textAlign: 'center',
            mb: { xs: 6, sm: 8, md: 10 },
          }}
        >
          <Typography
            variant={isMobile ? 'h3' : isTablet ? 'h2' : 'h1'}
            sx={{
              fontWeight: 800,
              mb: { xs: 2, sm: 3 },
              background: 'linear-gradient(45deg, #1976d2 30%, #42a5f5 90%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              letterSpacing: '-0.02em',
            }}
          >
            Your AI Document Analyst
          </Typography>
          <Typography
            variant={isMobile ? 'body1' : 'h5'}
            color="text.secondary"
            sx={{
              mb: { xs: 3, sm: 4 },
              maxWidth: '800px',
              mx: 'auto',
              lineHeight: 1.6,
              px: { xs: 2, sm: 0 },
            }}
          >
            Transform the way you interact with documents. Upload files, ask questions,
            and get intelligent insights powered by advanced AI technology.
          </Typography>
          <Box
            sx={{
              display: 'flex',
              gap: 2,
              justifyContent: 'center',
              flexDirection: { xs: 'column', sm: 'row' },
              px: { xs: 2, sm: 0 },
            }}
          >
            <Button
              variant="contained"
              size="large"
              onClick={handleGetStarted}
              sx={{
                borderRadius: 3,
                px: { xs: 3, sm: 5 },
                py: { xs: 1.5, sm: 2 },
                fontSize: { xs: '1rem', sm: '1.1rem' },
                fontWeight: 600,
                textTransform: 'none',
                boxShadow: '0 4px 14px rgba(25,118,210,0.3)',
                '&:hover': {
                  boxShadow: '0 6px 20px rgba(25,118,210,0.4)',
                  transform: 'translateY(-2px)',
                },
                transition: 'all 0.3s ease',
              }}
            >
              {isAuthenticated ? 'Go to Chat' : 'Get Started Free'}
            </Button>
            <Button
              variant="outlined"
              size="large"
              onClick={() => navigate('/')}
              sx={{
                borderRadius: 3,
                px: { xs: 3, sm: 5 },
                py: { xs: 1.5, sm: 2 },
                fontSize: { xs: '1rem', sm: '1.1rem' },
                fontWeight: 600,
                textTransform: 'none',
                borderWidth: 2,
                '&:hover': {
                  borderWidth: 2,
                  transform: 'translateY(-2px)',
                },
                transition: 'all 0.3s ease',
              }}
            >
              Learn More
            </Button>
          </Box>
        </Box>

        <Box sx={{ mt: { xs: 6, sm: 8, md: 10 } }}>
          <Typography
            variant={isMobile ? 'h4' : 'h3'}
            sx={{
              fontWeight: 700,
              textAlign: 'center',
              mb: { xs: 4, sm: 6 },
            }}
          >
            Why Choose Us?
          </Typography>
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: {
                xs: '1fr',
                sm: 'repeat(2, 1fr)',
                md: 'repeat(3, 1fr)',
              },
              gap: { xs: 2, sm: 3, md: 4 },
            }}
          >
            {features.map((feature, index) => (
              <Card
                key={index}
                sx={{
                  height: '100%',
                  borderRadius: 3,
                  boxShadow: '0 2px 12px rgba(0,0,0,0.08)',
                  transition: 'all 0.3s ease',
                  '&:hover': {
                    boxShadow: '0 8px 24px rgba(0,0,0,0.12)',
                    transform: 'translateY(-4px)',
                  },
                }}
              >
                  <CardContent
                    sx={{
                      p: { xs: 2.5, sm: 3 },
                      '&:last-child': { pb: { xs: 2.5, sm: 3 } },
                    }}
                  >
                    <Box
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        width: { xs: 60, sm: 70 },
                        height: { xs: 60, sm: 70 },
                        borderRadius: 2,
                        bgcolor: 'primary.main',
                        color: 'white',
                        mb: 2,
                        mx: 'auto',
                      }}
                    >
                      {feature.icon}
                    </Box>
                    <Typography
                      variant="h6"
                      sx={{
                        fontWeight: 600,
                        mb: 1.5,
                        textAlign: 'center',
                      }}
                    >
                      {feature.title}
                    </Typography>
                    <Typography
                      variant="body2"
                      color="text.secondary"
                      sx={{
                        textAlign: 'center',
                        lineHeight: 1.6,
                      }}
                    >
                      {feature.description}
                    </Typography>
                  </CardContent>
                </Card>
            ))}
          </Box>
        </Box>

        <Box
          sx={{
            mt: { xs: 6, sm: 8, md: 10 },
            p: { xs: 3, sm: 4, md: 6 },
            borderRadius: 4,
            background: 'linear-gradient(135deg, #1976d2 0%, #42a5f5 100%)',
            color: 'white',
            textAlign: 'center',
          }}
        >
          <Typography
            variant={isMobile ? 'h5' : 'h4'}
            sx={{
              fontWeight: 700,
              mb: 2,
            }}
          >
            Ready to revolutionize your research?
          </Typography>
          <Typography
            variant="body1"
            sx={{
              mb: { xs: 3, sm: 4 },
              opacity: 0.95,
              maxWidth: '600px',
              mx: 'auto',
            }}
          >
            Join thousands of researchers who are already using our AI-powered platform to
            accelerate their work.
          </Typography>
          <Button
            variant="contained"
            size="large"
            onClick={handleGetStarted}
            sx={{
              bgcolor: 'white',
              color: 'primary.main',
              borderRadius: 3,
              px: { xs: 3, sm: 5 },
              py: { xs: 1.5, sm: 2 },
              fontSize: { xs: '1rem', sm: '1.1rem' },
              fontWeight: 600,
              textTransform: 'none',
              boxShadow: '0 4px 14px rgba(0,0,0,0.2)',
              '&:hover': {
                bgcolor: 'grey.100',
                boxShadow: '0 6px 20px rgba(0,0,0,0.3)',
                transform: 'translateY(-2px)',
              },
              transition: 'all 0.3s ease',
            }}
          >
            {isAuthenticated ? 'Start Chatting' : 'Sign Up Now'}
          </Button>
        </Box>
      </Container>
    </Box>
  );
};

export default Hero;
