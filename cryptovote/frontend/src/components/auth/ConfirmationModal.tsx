import React from 'react';
import '../../styles/voter-auth.css';

type Props = {
  isOpen: boolean;
  title: string;
  message: string;
  onConfirm: () => void;
  onCancel: () => void;
};

const ConfirmationModal: React.FC<Props> = ({
  isOpen,
  title,
  message,
  onConfirm,
  onCancel,
}) => {
  if (!isOpen) return null;

  return (
    <div className="auth-modal-overlay">
      <div className="auth-modal-card">
        <h2 className="auth-h2">
          {title}
        </h2>
        <p className="auth-copy">{message}</p>
        <div className="flex justify-end gap-3">
          <button
            onClick={onCancel}
            className="auth-row-btn"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            className="auth-submit"
          >
            Sure
          </button>
        </div>
      </div>
    </div>
  );
};

export default ConfirmationModal;
