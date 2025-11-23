import React from 'react';
import Layout from './components/Layout';
import ChatInterface from './components/Chat/ChatInterface';
import { ThemeProvider } from './context/ThemeContext';

function App() {
  return (
    <ThemeProvider defaultTheme="dark" storageKey="nexus-ui-theme">
      <Layout>
        <ChatInterface />
      </Layout>
    </ThemeProvider>
  );
}

export default App;
