import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import { AuthProvider } from './contexts/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';

// Mock contexts
const mockAuthContext = {
  user: { id: 1, username: 'testuser', email: 'test@example.com' },
  login: jest.fn(),
  logout: jest.fn(),
  isAuthenticated: true,
  loading: false,
};

const mockThemeContext = {
  darkMode: false,
  toggleTheme: jest.fn(),
};

// Create test wrapper
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <ThemeProvider>
            {children}
          </ThemeProvider>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
};

describe('App Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders without crashing', () => {
    render(
      <TestWrapper>
        <App />
      </TestWrapper>
    );

    expect(screen.getByText(/nocbrain/i)).toBeInTheDocument();
  });

  test('renders dashboard by default', async () => {
    render(
      <TestWrapper>
        <App />
      </TestWrapper>
    );

    // Wait for components to load
    await waitFor(() => {
      expect(screen.getByText(/dashboard/i)).toBeInTheDocument();
    });
  });

  test('navigation works correctly', async () => {
    render(
      <TestWrapper>
        <App />
      </TestWrapper>
    );

    // Check if navigation items are present
    const networkLink = screen.getByText(/network/i);
    const securityLink = screen.getByText(/security/i);
    const knowledgeLink = screen.getByText(/knowledge/i);

    expect(networkLink).toBeInTheDocument();
    expect(securityLink).toBeInTheDocument();
    expect(knowledgeLink).toBeInTheDocument();
  });

  test('theme toggle works', async () => {
    render(
      <TestWrapper>
        <App />
      </TestWrapper>
    );

    // Find theme toggle button
    const themeButton = screen.getByRole('button', { name: /theme/i });
    expect(themeButton).toBeInTheDocument();

    // Click to toggle theme
    fireEvent.click(themeButton);
    expect(mockThemeContext.toggleTheme).toHaveBeenCalled();
  });
});

// Test Auth Context
describe('AuthContext', () => {
  test('provides authentication state', () => {
    const TestComponent = () => {
      const { isAuthenticated, user } = useAuth();
      return (
        <div>
          <span>{isAuthenticated ? 'Authenticated' : 'Not Authenticated'}</span>
          {user && <span>{user.username}</span>}
        </div>
      );
    };

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    expect(screen.getByText('Authenticated')).toBeInTheDocument();
    expect(screen.getByText('testuser')).toBeInTheDocument();
  });
});

// Test Theme Context
describe('ThemeContext', () => {
  test('provides theme state', () => {
    const TestComponent = () => {
      const { darkMode, toggleTheme } = useTheme();
      return (
        <div>
          <span>{darkMode ? 'Dark' : 'Light'}</span>
          <button onClick={toggleTheme}>Toggle</button>
        </div>
      );
    };

    render(
      <ThemeProvider>
        <TestComponent />
      </ThemeProvider>
    );

    expect(screen.getByText('Light')).toBeInTheDocument();
  });
});

// Test Protected Route
describe('ProtectedRoute', () => {
  test('allows authenticated users', () => {
    const TestComponent = () => <div>Protected Content</div>;

    render(
      <TestWrapper>
        <ProtectedRoute>
          <TestComponent />
        </ProtectedRoute>
      </TestWrapper>
    );

    expect(screen.getByText('Protected Content')).toBeInTheDocument();
  });
});

export {};
