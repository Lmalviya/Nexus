import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import ChatInterface from './components/Chat/ChatInterface';
import Home from './pages/Home';
import Login from './pages/Login';
import Register from './pages/Register';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import { ConversationProvider } from './context/ConversationContext';
import { UploadProvider } from './context/UploadContext';

// Protected Route Component
const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) return <div>Loading...</div>;

  if (!user) {
    return <Navigate to="/login" />;
  }

  return children;
};

// Main App Component
function App() {
  return (
    <AuthProvider>
      <ThemeProvider defaultTheme="dark" storageKey="nexus-ui-theme">
        <ConversationProvider>
          <UploadProvider>
            <Router>
              <Routes>
                <Route path="/" element={<Home />} />
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />

                <Route path="/chat" element={
                  <ProtectedRoute>
                    <Layout>
                      <ChatInterface />
                    </Layout>
                  </ProtectedRoute>
                } />
              </Routes>
            </Router>
          </UploadProvider>
        </ConversationProvider>
      </ThemeProvider>
    </AuthProvider>
  );
}

export default App;
