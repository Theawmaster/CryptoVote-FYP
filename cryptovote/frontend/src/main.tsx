import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './styles/index.css';
import { CredentialProvider } from './ctx/CredentialContext';

const rootElement = document.getElementById('root');

if (rootElement) {
  const root = ReactDOM.createRoot(rootElement);
  root.render(
    <React.StrictMode>
      <CredentialProvider>   
        <App />
      </CredentialProvider>
    </React.StrictMode>
  );
} else {
  console.error('❌ No root element found. Check index.html');
}
