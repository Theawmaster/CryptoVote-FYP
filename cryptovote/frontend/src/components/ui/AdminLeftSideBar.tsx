import React from 'react';
import Brand from '../Brand';
import LogoutButton from '../LogoutButton';
import '../../styles/admin-landing.css';

type Props = {
  title?: string;
};

const LeftSidebar: React.FC<Props> = ({ title = 'Admin Landing Page' }) => {
  return (
    <aside className="left-panel">
      <div className="sidebar-center">
        <div className="brand-wrap brand-wrap--center">
          <Brand title={title} />
        </div>

        <div className="sidebar-actions">
          <LogoutButton />
        </div>
      </div>
    </aside>
  );
};

export default LeftSidebar;
