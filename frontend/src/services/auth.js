function generateSessionId() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
    });
}

export const authService = {
    getSessionId: () => {
        let id = localStorage.getItem('sessionId');
        if (!id) {
            id = generateSessionId();
            localStorage.setItem('sessionId', id);
        }
        return id;
    },
    isAuthenticated: () => true,
    getCurrentUser: () => localStorage.getItem('sessionId'),
    getUserId: () => localStorage.getItem('sessionId'),
    logout: () => {
        localStorage.clear();
        window.location.href = '/';
    }
};
