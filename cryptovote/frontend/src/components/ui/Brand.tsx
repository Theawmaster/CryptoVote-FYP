import React from 'react';
import ntuLogo from '../../assets/logo/ntu_logo.png';
import cryptovoteLogo from '../../assets/logo/cryptovote_logo.png';

type BrandProps = {
  /** Text/JSX to show under the logos (editable). Defaults to "Voter Authentication". */
  title?: React.ReactNode;
  /** Extra classes on the outer wrapper */
  className?: string;
  /** Tailwind classes for the title text (fully overridable) */
  titleClassName?: string;
  /** Hide the title entirely if needed */
  showTitle?: boolean;
  /** Override sizes/styles per logo if needed */
  ntuClassName?: string;
  cryptoClassName?: string;
};

const Brand: React.FC<BrandProps> = ({
  title = 'Voter Authentication',
  className = '',
  titleClassName = 'mt-3 text-2xl md:text-3xl font-bold tracking-tight',
  showTitle = true,
  ntuClassName = 'mx-auto h-auto w-40 sm:w-44 md:w-48',
  cryptoClassName = 'mx-auto mt-3 h-auto w-24 sm:w-28 md:w-32',
}) => {
  return (
    <div className={`mb-6 text-center ${className}`}>
      <img src={ntuLogo} alt="NTU Logo" className={ntuClassName} />
      <img src={cryptovoteLogo} alt="CryptoVote Logo" className={cryptoClassName} />
      {showTitle && <div className={titleClassName}>{title}</div>}
    </div>
  );
};

export default Brand;
