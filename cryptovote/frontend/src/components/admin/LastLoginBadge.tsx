import { fmtAbs, fmtRel } from '../../utils/dates';
import type { AdminMe } from '../../services/admin/types';

export default function LastLoginBadge({ me }: { me: AdminMe | null }) {
  return (
    <span
      className="mgr-lastlogin-chip"
      title={
        me
          ? `Last login: ${fmtAbs(me.last_login_at)} (Asia/Singapore)` +
            (me.last_login_ip ? ` • IP: ${me.last_login_ip}` : '')
          : 'Last login: —'
      }
      aria-label="Last login"
    >
      <svg width="16" height="16" viewBox="0 0 24 24" style={{ opacity: 0.8 }}>
        <path fill="currentColor" d="M12 1a11 11 0 1 0 11 11A11.012 11.012 0 0 0 12 1Zm1 11.59V7h-2v6h6v-2Z"/>
      </svg>
      <span className="mgr-chip-label">Last login</span>
      <span>• {fmtAbs(me?.last_login_at)} (SGT)</span>
      <span className="mgr-chip-muted">• {fmtRel(me?.last_login_at)}</span>
    </span>
  );
}
