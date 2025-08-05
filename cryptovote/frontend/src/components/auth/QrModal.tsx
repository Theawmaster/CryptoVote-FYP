import React from 'react';

type QrModalProps = {
  open: boolean;
  onClose: () => void;
  totpUri: string | null;
  qrDataUrl: string | null; // can be null while generating
};

const QrModal: React.FC<QrModalProps> = ({ open, onClose, totpUri, qrDataUrl }) => {
  if (!open) return null;

  return (
    <div className="auth-modal-overlay">
      <div className="auth-modal-card">
        <h3 className="text-lg font-semibold mb-2">
          Scan with your authenticator
        </h3>

        {qrDataUrl ? (
          <img
            src={qrDataUrl}
            alt="TOTP QR"
            className="mx-auto mb-3 w-56 h-56"
          />
        ) : (
          <div className="w-56 h-56 mx-auto mb-3 rounded bg-gray-200 dark:bg-gray-700 animate-pulse" />
        )}

        {totpUri && (
          <p className="text-xs text-gray-600 dark:text-gray-300 break-all mb-3">
            {totpUri}
          </p>
        )}

        <div className="flex justify-center gap-2">
          {qrDataUrl && (
            <a
              href={qrDataUrl}
              download="cryptovote-totp.png"
              className="auth-submit px-3 py-2"
            >
              Download
            </a>
          )}
          <button
            onClick={onClose}
            className="auth-row-btn px-3 py-2"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default QrModal;
