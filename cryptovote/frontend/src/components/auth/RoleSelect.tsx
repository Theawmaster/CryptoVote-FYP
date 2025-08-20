import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

type Props = {
  className?: string;
  size?: 'sm' | 'md';
  label?: string; // accessible label
};

const RoleSelect: React.FC<Props> = ({ className = '', size = 'md', label = 'Select role' }) => {
  const nav = useNavigate();
  const { pathname } = useLocation();
  const value = pathname.startsWith('/auth/admin') ? 'admin' : 'voter';

  const pad = size === 'sm' ? 'px-3 py-1.5 text-sm' : 'px-4 py-2 text-sm md:text-base';

  return (
    <div className={`relative inline-block group ${className}`}>
      <label className="sr-only">{label}</label>
      <select
        aria-label={label}
        value={value}
        onChange={(e) => nav(e.target.value === 'admin' ? '/auth/admin' : '/auth/voter')}
        className={`appearance-none rounded-full border border-gray-300 dark:border-gray-700
                    bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100
                    ${pad} pr-10 shadow-sm focus:outline-none focus:ring-2 focus:ring-teal-500
                    cursor-pointer transition group-hover:border-teal-500 group-hover:bg-gray-50
                    dark:group-hover:bg-gray-700/60`}
      >
        <option value="voter">Voter</option>
        <option value="admin">Admin</option>
      </select>

      {/* chevron */}
      <svg
        className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4
                  text-gray-500 dark:text-gray-400 group-hover:text-teal-600"
        viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"
      >
        <path fillRule="evenodd" d="M5.23 7.21a.75.75 0 011.06.02L10 10.94l3.71-3.71a.75.75 0 111.06 1.06l-4.24 4.24a.75.75 0 01-1.06 0L5.21 8.29a.75.75 0 01.02-1.08z" clipRule="evenodd" />
      </svg>
    </div>
  );
};

export default RoleSelect;
