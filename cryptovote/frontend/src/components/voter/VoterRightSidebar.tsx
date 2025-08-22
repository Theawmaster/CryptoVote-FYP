import React from 'react';
import Brand from '../ui/Brand';
import LogoutButton from '../auth/LogoutButton';

type Props = {
  title?: React.ReactNode;
  showLogout?: boolean;
};

const VoterRightSidebar: React.FC<Props> = ({
  title = 'Voter Dashboard',
  showLogout = true,
}) => {
  return (
    <aside className="right-panel-voter">
      <div className="sidebar-center">
        <div className="brand-wrap brand-wrap--center">
          <Brand
            title={title}
            titleClassName="mt-3 text-2xl md:text-3xl font-bold tracking-tight"
            ntuClassName="mx-auto h-auto w-40 sm:w-44 md:w-48"
            cryptoClassName="mx-auto mt-3 h-auto w-24 sm:w-28 md:w-32"
          />
        </div>

        {showLogout && (
          <div className="sidebar-actions">
            <LogoutButton />
          </div>
        )}
      </div>
    </aside>
  );
};

export default VoterRightSidebar;
