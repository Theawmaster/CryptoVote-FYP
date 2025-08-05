import React, { useEffect } from 'react';

type ToastProps = {
  type: 'success' | 'error' | 'info';
  message: string;
  duration?: number; // ms
  onClose?: () => void;
};

const Toast: React.FC<ToastProps> = ({ type, message, duration = 3000, onClose }) => {
  useEffect(() => {
    const t = setTimeout(() => onClose?.(), duration);
    return () => clearTimeout(t);
  }, [duration, onClose]);

  const toastClass =
    type === 'success'
      ? 'auth-toast--success'
      : type === 'error'
      ? 'auth-toast--error'
      : 'auth-toast--info'; // now info gets its own style

  return (
    <div
      className={['auth-toast', toastClass].join(' ')}
      role="status"
      aria-live="polite"
    >
      {message}
    </div>
  );
};

export default Toast;
