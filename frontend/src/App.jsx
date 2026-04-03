
import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';

import Dashboard from './pages/Dashboard';
import ChatPage from './pages/ChatPage';
import Profile from './pages/Profile';
import AnimatedBackground from './components/AnimatedBackground';

const NotFound = () => <div className="container" style={{ paddingTop: '4rem', textAlign: 'center' }}><h1>404 - Not Found</h1></div>;

function App() {
    return (
        <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
            <AnimatedBackground />
            <div className="app-layout">

                <Routes>
                    <Route path="/" element={<Dashboard />} />
                    <Route path="/chat" element={<ChatPage />} />
                    <Route path="/profile" element={<Profile />} />
                    <Route path="*" element={<NotFound />} />
                </Routes>
            </div>
        </BrowserRouter>
    );
}

export default App;
