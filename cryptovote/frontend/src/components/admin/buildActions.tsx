import {
  startElection, endElection, tallyElection, downloadReportFile,
} from '../../services/admin/electionActions';
import type { ElectionStatus, ModalKind } from '../../services/admin/types';

type Params = {
  electionId: string;
  status: ElectionStatus | null;
  reportFormat: 'pdf' | 'csv';
  onAfter?: () => Promise<void> | void;      // e.g., refresh()
  toast?: (t:'success'|'error'|'info', m:string)=>void;
};

export function buildActions(p: Params) {
  const name = p.status?.name ?? 'this election';

  return {
    start: {
      title: 'Start Election',
      message: `Start "${name}" now? This will mark it as Active.`,
      disabled: !!p.status?.has_started,
      label: (busy:boolean) => busy ? 'Starting…' : 'Start Election',
      run: async () => {
        await startElection(p.electionId);
        p.toast?.('success', 'Election started.');
        await p.onAfter?.();
      },
    },
    end: {
      title: 'End Election',
      message: `End "${name}" now? This action cannot be undone.`,
      disabled: !p.status?.is_active || !!p.status?.has_ended,
      label: (busy:boolean) => busy ? 'Ending…' : 'End Election',
      danger: true,
      run: async () => {
        await endElection(p.electionId);
        p.toast?.('success', 'Election ended.');
        await p.onAfter?.();
      },
    },
    tally: {
      title: 'Tally Election',
      message: `Generate the homomorphic tally for "${name}"? This requires the election to have ended.`,
      disabled: !p.status?.has_ended || !!p.status?.tally_generated,
      label: (busy:boolean) =>
        busy ? 'Tallying…' : (p.status?.tally_generated ? 'Tally Generated' : 'Tally Election'),
      run: async () => {
        await tallyElection(p.electionId);
        p.toast?.('success', 'Tally generated.');
        await p.onAfter?.();
      },
    },
    report: {
      title: 'Generate Report',
      message: `Generate a ${p.reportFormat.toUpperCase()} report for "${name}"?`,
      disabled: !p.status?.tally_generated,
      label: (busy:boolean) => busy ? 'Preparing…' : 'Generate Report',
      run: async () => {
        await downloadReportFile(p.electionId, p.reportFormat);
        p.toast?.('success', `Report (${p.reportFormat.toUpperCase()}) downloaded.`);
      },
    },
  } as const satisfies Record<Exclude<ModalKind,null>, {
    title: string; message: string; disabled: boolean; label: (busy:boolean)=>string;
    danger?: boolean; run: () => Promise<void>;
  }>;
}
