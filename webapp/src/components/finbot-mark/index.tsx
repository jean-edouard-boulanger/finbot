import React from "react";

export interface FinbotMarkProps extends React.SVGProps<SVGSVGElement> {}

export const FinbotMark: React.FC<FinbotMarkProps> = (props) => {
  return (
    <svg viewBox="0 0 64 64" aria-hidden="true" {...props}>
      <rect
        x="3"
        y="3"
        width="58"
        height="58"
        rx="15"
        fill="currentColor"
        fillOpacity="0.12"
      />
      <rect
        x="3"
        y="3"
        width="58"
        height="58"
        rx="15"
        fill="none"
        stroke="currentColor"
        strokeOpacity="0.35"
        strokeWidth="2"
      />
      <rect x="17" y="36" width="8" height="14" rx="2" fill="currentColor" />
      <rect x="28" y="28" width="8" height="22" rx="2" fill="currentColor" />
      <rect x="39" y="18" width="8" height="32" rx="2" fill="currentColor" />
    </svg>
  );
};
