import React from 'react';

type Props = {
  open: boolean;
  title?: string;
  message?: string;
  onStay: () => void;
  onLeave: () => void;
};

export default function ConfirmLeaveModal({
  open,
  title = 'Leave this page?',
  message = 'You have an in-progress action. If you leave, it will be cancelled.',
  onStay,
  onLeave,
}: Props) {
  if (!open) return null;
  return (
    <div className="session-modal-backdrop" role="dialog" aria-modal="true">
      <div className="session-modal">
        <h3>{title}</h3>
        <p>{message}</p>
        <div className="session-actions">
          <button className="btn btn-outline" onClick={onStay}>Stay</button>
          <button className="btn btn-primary" onClick={onLeave}>Leave</button>
        </div>
      </div>
    </div>
  );
}
