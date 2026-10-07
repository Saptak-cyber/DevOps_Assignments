import { useEffect, useRef, useState } from 'react';
import { api } from '../api.js';
import { hhmm } from '../time.js';

const DURATIONS = [15, 20, 30, 45, 60, 90];

// One dialog for both booking and rescheduling. `draft` carries the prefill.
export default function BookingDialog({ draft, doctors, onClose, onSaved }) {
  const ref = useRef(null);
  const editing = Boolean(draft?.appointment);
  const [form, setForm] = useState(null);
  const [mode, setMode] = useState('new');
  const [matches, setMatches] = useState([]);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!draft) return;
    const a = draft.appointment;
    setForm({
      doctor_id: String(a?.doctor.id ?? draft.doctorId ?? doctors[0]?.id ?? ''),
      date: a ? a.scheduled_at.slice(0, 10) : draft.date,
      time: a ? a.scheduled_at.slice(11, 16) : hhmm(draft.minutes ?? 9 * 60),
      duration_minutes: String(a?.duration_minutes ?? 30),
      reason: a?.reason ?? '',
      full_name: '',
      phone: '',
      query: '',
      patient_id: '',
    });
    setMode('new');
    setError('');
    setMatches([]);
    ref.current?.showModal();
  }, [draft, doctors]);

  // Search returning patients as the receptionist types.
  useEffect(() => {
    if (mode !== 'returning' || !form) return undefined;
    const t = setTimeout(() => {
      api
        .patients(form.query.trim())
        .then(setMatches)
        .catch(() => setMatches([]));
    }, 200);
    return () => clearTimeout(t);
  }, [mode, form?.query]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!draft || !form) return <dialog ref={ref} className="dialog" />;

  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }));

  function close() {
    ref.current?.close();
    onClose();
  }

  async function submit(event) {
    event.preventDefault();
    setSaving(true);
    setError('');
    const timing = {
      doctor_id: Number(form.doctor_id),
      scheduled_at: `${form.date}T${form.time}`,
      duration_minutes: Number(form.duration_minutes),
      reason: form.reason.trim(),
    };
    try {
      let saved;
      if (editing) {
        saved = await api.update(draft.appointment.id, timing);
      } else if (mode === 'returning') {
        if (!form.patient_id) throw new Error('Choose a patient from the list, or switch to New patient.');
        saved = await api.book({ ...timing, patient_id: Number(form.patient_id) });
      } else {
        saved = await api.book({ ...timing, patient: { full_name: form.full_name.trim(), phone: form.phone.trim() } });
      }
      ref.current?.close();
      onSaved(saved, editing ? 'Appointment moved' : 'Appointment booked');
    } catch (e) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <dialog ref={ref} className="dialog" onCancel={close} aria-labelledby="dialog-title">
      <form onSubmit={submit}>
        <h2 id="dialog-title">
          {editing ? `Reschedule ${draft.appointment.patient.full_name}` : 'Book an appointment'}
        </h2>

        {!editing && (
          <fieldset className="patient-switch">
            <legend>Patient</legend>
            <label>
              <input type="radio" name="mode" checked={mode === 'new'} onChange={() => setMode('new')} /> New patient
            </label>
            <label>
              <input type="radio" name="mode" checked={mode === 'returning'} onChange={() => setMode('returning')} />{' '}
              Returning patient
            </label>
          </fieldset>
        )}

        {!editing && mode === 'new' && (
          <div className="row">
            <label className="field">
              <span>Full name</span>
              <input required minLength={2} value={form.full_name} onChange={set('full_name')} autoComplete="off" />
            </label>
            <label className="field">
              <span>Phone</span>
              <input
                required
                type="tel"
                pattern="\+?[0-9][0-9 \-]{6,18}"
                placeholder="+91 98765 43210"
                value={form.phone}
                onChange={set('phone')}
              />
            </label>
          </div>
        )}

        {!editing && mode === 'returning' && (
          <div className="row">
            <label className="field">
              <span>Search by name or phone</span>
              <input value={form.query} onChange={set('query')} autoComplete="off" />
            </label>
            <label className="field">
              <span>Patient</span>
              <select required value={form.patient_id} onChange={set('patient_id')}>
                <option value="">{matches.length ? 'Choose a patient' : 'No matches yet'}</option>
                {matches.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.full_name} ({p.phone})
                  </option>
                ))}
              </select>
            </label>
          </div>
        )}

        <label className="field">
          <span>Doctor</span>
          <select value={form.doctor_id} onChange={set('doctor_id')}>
            {doctors.map((d) => (
              <option key={d.id} value={d.id}>
                {d.full_name}, {d.specialty}
              </option>
            ))}
          </select>
        </label>

        <div className="row row-3">
          <label className="field">
            <span>Date</span>
            <input required type="date" value={form.date} onChange={set('date')} />
          </label>
          <label className="field">
            <span>Start</span>
            <input required type="time" step={300} value={form.time} onChange={set('time')} />
          </label>
          <label className="field">
            <span>Length</span>
            <select value={form.duration_minutes} onChange={set('duration_minutes')}>
              {DURATIONS.map((m) => (
                <option key={m} value={m}>
                  {m} min
                </option>
              ))}
            </select>
          </label>
        </div>

        <label className="field">
          <span>Reason for visit</span>
          <input maxLength={200} value={form.reason} onChange={set('reason')} placeholder="Fever for three days" />
        </label>

        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}

        <div className="dialog-actions">
          <button type="button" className="btn btn-quiet" onClick={close}>
            Close
          </button>
          <button type="submit" className="btn btn-primary" disabled={saving}>
            {editing ? 'Move appointment' : 'Book appointment'}
          </button>
        </div>
      </form>
    </dialog>
  );
}
