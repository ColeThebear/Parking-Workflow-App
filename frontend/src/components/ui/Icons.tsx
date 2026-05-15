/** Minimal inline SVG icon set — no external dependency required. */

type IconProps = { className?: string };

const base = "w-5 h-5 shrink-0";

export function IconDashboard({ className = base }: IconProps) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.75}>
      <rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" />
      <rect x="3" y="14" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" />
    </svg>
  );
}

export function IconCar({ className = base }: IconProps) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.75}>
      <path d="M5 11l2-5h10l2 5" /><rect x="3" y="11" width="18" height="7" rx="2" />
      <circle cx="7.5" cy="18" r="1.5" /><circle cx="16.5" cy="18" r="1.5" />
    </svg>
  );
}

export function IconClock({ className = base }: IconProps) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.75}>
      <circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 3" />
    </svg>
  );
}

export function IconSearch({ className = base }: IconProps) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.75}>
      <circle cx="11" cy="11" r="7" /><path d="M16.5 16.5l4 4" />
    </svg>
  );
}

export function IconTicket({ className = base }: IconProps) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.75}>
      <rect x="3" y="6" width="18" height="13" rx="2" />
      <path d="M3 10h18M8 6V4M16 6V4" />
    </svg>
  );
}

export function IconUpload({ className = base }: IconProps) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.75}>
      <path d="M12 16V4m-4 4l4-4 4 4" /><path d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2" />
    </svg>
  );
}

export function IconUsers({ className = base }: IconProps) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.75}>
      <circle cx="9" cy="7" r="4" /><path d="M3 21v-2a4 4 0 014-4h4a4 4 0 014 4v2" />
      <path d="M16 3.13a4 4 0 010 7.75M21 21v-2a4 4 0 00-3-3.87" />
    </svg>
  );
}

export function IconSessions({ className = base }: IconProps) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.75}>
      <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2" />
      <rect x="9" y="3" width="6" height="4" rx="1" /><path d="M9 12h6M9 16h4" />
    </svg>
  );
}

export function IconWallet({ className = base }: IconProps) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.75}>
      <rect x="2" y="7" width="20" height="14" rx="2" />
      <path d="M16 14a1 1 0 100-2 1 1 0 000 2z" fill="currentColor" stroke="none" />
      <path d="M2 11h20M6 7V5a2 2 0 012-2h8a2 2 0 012 2v2" />
    </svg>
  );
}

export function IconShield({ className = base }: IconProps) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.75}>
      <path d="M12 3L4 6v6c0 5.25 3.5 9.74 8 11 4.5-1.26 8-5.75 8-11V6l-8-3z" />
      <path d="M9 12l2 2 4-4" />
    </svg>
  );
}

export function IconMenu({ className = base }: IconProps) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.75}>
      <path d="M3 6h18M3 12h18M3 18h18" />
    </svg>
  );
}

export function IconChevronLeft({ className = base }: IconProps) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path d="M15 18l-6-6 6-6" />
    </svg>
  );
}

export function IconLogout({ className = base }: IconProps) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.75}>
      <path d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h6a2 2 0 012 2v1" />
    </svg>
  );
}
