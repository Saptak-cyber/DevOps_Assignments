import { useEffect, useState } from 'react';
import { clock, formatDuration } from '../time.js';
import { NEXT_ACTIONS, STATUSES, statusClass } from '../status.js';

function actionLabel(from, to) {
  if (to === 'SCHEDULED') return from === 'CHECKED_IN' ? 'Undo check-in' : 'Mark as expected';
  if (to === 'CHECKED_IN' && from === 'COMPLETED') return 'Reopen visit';
  return STATUSES[to].verb;
}

export function StatusTag({ status }) {
  return <span className={`tag ${statusClass(status)}`}>{STATUSES[status].label}</span>;
}

function Detail({ appt, busy, onStatus, onCancel, onSaveNotes, onReschedule, onClose }) {
  const [notes, setNotes] = useState(appt.notes);
  const [confirmCancel, setConfirmCancel] = useState(false);
  useEffect(() => {
    setNotes(appt.notes);
    setConfirmCancel(false);
  }, [appt.id, appt.notes]);

  const locked = appt.status === 'CANCELLED';

  return (
    <article className="detail" aria-live="polite">
      <div className="detail-top">
        <StatusTag status={appt.status} />
        <button type="button" className="link" onClick={onClose}>
          Back to the list
        </button>
      </div>
      <h2>{appt.patient.full_name}</h2>
      <p className="detail-when">
        {clock(appt.scheduled_at)} to {clock(appt.ends_at)} ({formatDuration(appt.duration_minutes)}) with{' '}
        {appt.doctor.full_name}
      </p>
      <dl>
        <dt>Phone</dt>
        <dd>
          <a href={`tel:${appt.patient.phone.replace(/\s/g, '')}`}>{appt.patient.phone}</a>
        </dd>
        <dt>Reason</dt>
        <dd>{appt.reason || 'Not given'}</dd>
        <dt>Room</dt>
        <dd>{appt.doctor.room}</dd>
      </dl>

      {!locked && (
        <div className="actions">
          {NEXT_ACTIONS[appt.status]
            .filter((s) => s !== 'CANCELLED')
            .map((s) => (
              <button key={s} type="button" className="btn" disabled={busy} onClick={() => onStatus(appt.id, s)}>
                {actionLabel(appt.status, s)}
              </button>
            ))}
          {appt.status !== 'COMPLETED' && (
            <button type="button" className="btn btn-quiet" disabled={busy} onClick={() => onReschedule(appt)}>
              Reschedule
            </button>
          )}
        </div>
      )}

      <label className="field">
        <span>Front-desk notes</span>
        <textarea
          rows={3}
          value={notes}
          disabled={locked}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Insurance card checked, prefers Hindi, etc."
        />
      </label>
      {!locked && notes !== appt.notes && (
        <button type="button" className="btn" disabled={busy} onClick={() => onSaveNotes(appt.id, notes)}>
          Save notes
        </button>
      )}

      {NEXT_ACTIONS[appt.status].includes('CANCELLED') && (
        <div className="danger-zone">
          {confirmCancel ? (
            <>
              <p>Cancel this appointment? The slot becomes free for other patients.</p>
              <button type="button" className="btn btn-danger" disabled={busy} onClick={() => onCancel(appt.id)}>
                Cancel appointment
              </button>
              <button type="button" className="link" onClick={() => setConfirmCancel(false)}>
                Keep it
              </button>
            </>
          ) : (
            <button type="button" className="link link-danger" onClick={() => setConfirmCancel(true)}>
              Cancel appointment
            </button>
          )}
        </div>
      )}
      {locked && <p className="muted">Cancelled appointments can’t be changed. Book a new slot instead.</p>}
    </article>
  );
}

function Queue({ appointments, filter, onSelect }) {
  const rows = filter ? appointments.filter((a) => a.status === filter) : appointments;
  return (
    <div className="queue">
      <h2>{filter ? STATUSES[filter].label : 'Everyone today'}</h2>
      {rows.length === 0 ? (
        <p className="muted">
          {filter ? 'No one in this group right now.' : 'No appointments on this day. Click a doctor’s column to book one.'}
        </p>
      ) : (
        <ol>
          {rows.map((a) => (
            <li key={a.id}>
              <button type="button" onClick={() => onSelect(a.id)} className={statusClass(a.status)}>
                <span className="q-time">{clock(a.scheduled_at)}</span>
                <span className="q-main">
                  <strong>{a.patient.full_name}</strong>
                  <span>{a.doctor.full_name}</span>
                </span>
                <StatusTag status={a.status} />
              </button>
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}

export default function SidePanel(props) {
  const { selected } = props;
  return (
    <aside className="side">{selected ? <Detail appt={selected} {...props} /> : <Queue {...props} />}</aside>
  );
}
