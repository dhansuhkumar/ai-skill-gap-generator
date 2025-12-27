import React, { useEffect } from 'react';
import Header from './components/Header';
import Main from './components/Main';
import Footer from './components/Footer';
import './App.css';
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(import.meta.env.VITE_SUPABASE_URL, import.meta.env.VITE_SUPABASE_KEY);

function App() {
  useEffect(() => {
    const getSession = async () => {
      const { data, error } = await supabase.auth.getSession();
      if (error || !data.session) {
        window.location.href = 'login.html';
      } else {
        // Add the JWT to all subsequent requests
        const a = document.createElement("a");
        a.href = "/api";
        const apiUrl = a.href;

        const originalFetch = fetch;
        window.fetch = async (url, options) => {
          if (url.startsWith(apiUrl)) {
            const headers = new Headers(options ? options.headers : {})
            headers.set('Authorization', `Bearer ${data.session.access_token}`);
            
            const newOptions = {
              ...options,
              headers,
            };
            return originalFetch(url, newOptions);
          }
          return originalFetch(url, options);
        };
      }
    };
    getSession();
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
