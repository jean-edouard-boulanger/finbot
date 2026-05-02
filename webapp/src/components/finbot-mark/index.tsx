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
      <path
        d="M14 45 C 22 43, 26 30, 32 28 S 44 21, 50 15"
        fill="none"
        stroke="currentColor"
        strokeWidth="4"
        strokeLinecap="round"
      />
      <circle cx="50" cy="15" r="3.5" fill="currentColor" />
    </svg>
  );
};
