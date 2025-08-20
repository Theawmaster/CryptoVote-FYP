import React from 'react';
import type { ElectionStatus, ModalKind } from '../../services/admin/types';

export default function ActionColumn({
  status, busy, onOpen, reportFormat, setReportFormat, labels, disabled, dangerEnd,
}: {
  status: ElectionStatus;
  busy: ModalKind | null;
  onOpen: (k: Exclude<ModalKind,null>) => void;
  reportFormat: 'pdf'|'csv';
  setReportFormat: (f: 'pdf'|'csv') => void;
  labels: { start: string; end: string; tally: string; report: string };
  disabled: { start: boolean; end: boolean; tally: boolean; report: boolean };
  dangerEnd?: boolean;
}) {
  return (
    <div className="mgr-actions">
      <h3 className="mgr-actions__title">{status.name}</h3>

      <button className="mgr-btn"
              disabled={disabled.start || busy === 'start'}
              onClick={() => onOpen('start')}>
        {labels.start}
      </button>

      <button className="mgr-btn mgr-btn--outline"
              onClick={() => {/* toggled by parent via panel state */}}>
        Election Status
      </button>

      <button className={`mgr-btn ${dangerEnd ? 'mgr-btn--danger' : ''}`}
              disabled={disabled.end || busy === 'end'}
              onClick={() => onOpen('end')}
              title={!status.is_active ? 'Start election first' : status.has_ended ? 'Already ended' : ''}>
        {labels.end}
      </button>

      <button className="mgr-btn"
              disabled={disabled.tally || busy === 'tally'}
              onClick={() => onOpen('tally')}
              title={!status.has_ended ? 'End election first' : status.tally_generated ? 'Tally already generated' : ''}>
        {labels.tally}
      </button>

      <div className="mgr-report-row">
        <button className="mgr-btn"
                disabled={disabled.report || busy === 'report'}
                onClick={() => onOpen('report')}
                title={!status.tally_generated ? 'Generate tally first' : ''}>
          {labels.report}
        </button>

        <select className="mgr-select"
                value={reportFormat}
                onChange={e => setReportFormat(e.target.value as 'pdf'|'csv')}
                aria-label="Report format">
          <option value="pdf">PDF</option>
          <option value="csv">CSV</option>
        </select>
      </div>
    </div>
  );
}
