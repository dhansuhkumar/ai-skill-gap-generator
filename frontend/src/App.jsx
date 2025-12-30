import React, { useEffect } from 'react';
import Header from './components/Header';
import Main from './components/Main';
import Footer from './components/Footer';
import './App.css';
import { createClient } from '@supabase/supabase-js';
import { API_BASE_URL } from './config';

const supabase = createClient(import.meta.env.VITE_SUPABASE_URL, import.meta.env.VITE_SUPABASE_KEY);

function App() {
  useEffect(() => {
    const checkAuth = async () => {
      // Check local JWT - this is what we get from login.html
      const jwtToken = localStorage.getItem("jwtToken");

      if (!jwtToken) {
        console.warn("Authentication missing. Redirecting to login.");
        window.location.href = 'login.html';
        return;
      }

      // 3. Setup Fetch Interceptor
      const originalFetch = window.fetch;
      window.fetch = async (url, options = {}) => {
        const token = localStorage.getItem("jwtToken");

        // Inject Authorization header for requests to our Backend API
        if (url.toString().startsWith(API_BASE_URL) && token) {
          options.headers = {
            ...options.headers,
            'Authorization': `Bearer ${token}`
          };
        }
        return originalFetch(url, options);
      };
    };

    checkAuth();
  }, []);

  return (
    <div className="App">
      <Header />
      <Main />
      <Footer />
    </div>
  );
}

export default App;

