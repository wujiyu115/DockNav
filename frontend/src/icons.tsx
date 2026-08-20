import React from 'react';

const s = { strokeWidth: 1.8, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const };

export const Search = () => (
  <svg viewBox="0 0 24 24" {...s}><circle cx="11" cy="11" r="7" /><path d="M20 20l-4.2-4.2" /></svg>
);
export const Refresh = () => (
  <svg viewBox="0 0 24 24" {...s}><path d="M20 12a8 8 0 1 1-2.3-5.6" /><path d="M20 4v4h-4" /></svg>
);
export const Grid = () => (
  <svg viewBox="0 0 24 24" {...s}>
    <rect x="4" y="4" width="7" height="7" rx="2" /><rect x="13" y="4" width="7" height="7" rx="2" />
    <rect x="4" y="13" width="7" height="7" rx="2" /><rect x="13" y="13" width="7" height="7" rx="2" />
  </svg>
);
export const List = () => (
  <svg viewBox="0 0 24 24" {...s}><path d="M4 7h16M4 12h16M4 17h16" /></svg>
);
export const Sun = () => (
  <svg viewBox="0 0 24 24" {...s}>
    <circle cx="12" cy="12" r="4" />
    <path d="M12 3v2M12 19v2M3 12h2M19 12h2M5.6 5.6l1.4 1.4M17 17l1.4 1.4M18.4 5.6L17 7M7 17l-1.4 1.4" />
  </svg>
);
export const Moon = () => (
  <svg viewBox="0 0 24 24" {...s}><path d="M20 14.5A8.5 8.5 0 0 1 9.5 4a7 7 0 1 0 10.5 10.5z" /></svg>
);
export const Plug = () => (
  <svg viewBox="0 0 24 24" {...s}>
    <path d="M9 3v6M15 3v6M6 9h12v2a6 6 0 0 1-12 0z" /><path d="M12 17v4" />
  </svg>
);
export const External = () => (
  <svg viewBox="0 0 24 24" {...s}><path d="M14 4h6v6" /><path d="M20 4l-8 8" /><path d="M18 14v4a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4" /></svg>
);
