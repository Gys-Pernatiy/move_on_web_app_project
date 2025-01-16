import React from 'react';
import { createRoot, Container } from 'react-dom/client';
import App from './App.tsx';import eruda from 'eruda';

eruda.init();

const container = document.getElementById('root') as Container;
const root = createRoot(container);

window.Telegram.WebApp.ready();
window.Telegram.WebApp.expand();

if (window.visualViewport) {
    window.visualViewport.addEventListener('resize', () => {
        document.body.style.height = window.visualViewport?.height + 'px';
    });
}
window.addEventListener('scroll', () => {
    if (window.scrollY > 0) window.scrollTo(0, 0);
});

root.render(
    <React.StrictMode>
        <App />
    </React.StrictMode>
);