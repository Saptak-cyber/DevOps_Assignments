import { useCallback, useEffect, useMemo, useState } from 'react';
import { api } from './api.js';
import { longDate, shiftDay, todayIso } from './time.js';
import { STATUSES, statusClass } from './status.js';
import DayBoard from './components/DayBoard.jsx';
import SidePanel from './components/SidePanel.jsx';
import BookingDialog from './components/BookingDialog.jsx';

const REFRESH_MS = 30_000;
const FILTERS = ['SCHEDULED', 'CHECKED_IN', 'COMPLETED', 'NO_SHOW', 'CANCELLED'];
const STAT_KEY = { SCHEDULED: 'scheduled', CHECKED_IN: 'checked_in', COMPLETED: 'completed', NO_SHOW: 'no_show', CANCELLED: 'cancelled' };

function summary(stats, isToday) {
  if (!stats) return '';
  if (stats.total === 0) return isToday ? 'Nothing booked yet today.' : 'Nothing booked on this day.';
  const parts = [`${stats.total} appointment${stats.total === 1 ? '' : 's'}`];
  if (stats.checked_in) parts.push(`${stats.checked_in} waiting to be seen`);
  if (stats.scheduled) parts.push(`${stats.scheduled} still to arrive`);
  return `${parts.join(', ')}.`;
}

export default function App() {
  const [day, setDay] = useState(todayIso);
  const [doctors, setDoctors] = useState([]);
  const [appointments, setAppointments] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedId, setSelectedId] = useState(null);
  const [filter, setFilter] = useState(null);
  const [draft, setDraft] = useState(null);
  const [busy, setBusy] = useState(false);
  const [toast, setToast] = useState('');

  const isToday = day === todayIso();

  const load = useCallback(async () => {
    try {
      const [docs, appts, st] = await Promise.all([api.doctors(), api.appointments(day), api.stats(day)]);
      setDoctors(docs);
      setAppointments(appts);
      setStats(st);
      setError('');
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [day]);

  useEffect(() => {
    setLoading(true);
    setSelectedId(null);
    load();
    const t = setInterval(load, REFRESH_MS);
    return () => clearInterval(t);
  }, [load]);

  useEffect(() => {
    if (!toast) return undefined;
    const t = setTimeout(() => setToast(''), 3500);
    return () => clearTimeout(t);
  }, [toast]);

  const selected = useMemo(() => appointments.find((a) => a.id === selectedId) || null, [appointments, selectedId]);

  async function run(action, message) {
    setBusy(true);
    try {
      await action();
      setToast(message);
      await load();
    } catch (e) {
      setToast(e.message);
    } finally {
      setBusy(false);
    }
  }

  const handlers = {
    onStatus: (id, status) => run(() => api.update(id, { status }), `Marked as ${STATUSES[status].label.toLowerCase()}`),
    onCancel: (id) => run(() => api.cancel(id), 'Appointment cancelled'),
    onSaveNotes: (id, notes) => run(() => api.update(id, { notes }), 'Notes saved'),
    onReschedule: (appointment) => setDraft({ appointment }),
    onClose: () => setSelectedId(null),
  };

  function onSaved(saved, message) {
    setDraft(null);
    setToast(message);
    const savedDay = saved.scheduled_at.slice(0, 10);
    if (savedDay !== day) setDay(savedDay);
    else load();
    setSelectedId(saved.id);
  }

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <svg viewBox="0 0 32 32" aria-hidden="true">
            <rect width="32" height="32" rx="7" />
            <path d="M13 7h6v6h6v6h-6v6h-6v-6H7v-6h6z" />
          </svg>
          <span>ClinicDesk</span>
        </div>

        <nav className="daynav" aria-label="Choose day">
          <button type="button" className="icon-btn" onClick={() => setDay((d) => shiftDay(d, -1))} aria-label="Previous day">
            ‹
          </button>
          <input type="date" value={day} onChange={(e) => e.target.value && setDay(e.target.value)} aria-label="Day" />
          <button type="button" className="icon-btn" onClick={() => setDay((d) => shiftDay(d, 1))} aria-label="Next day">
            ›
          </button>
          {!isToday && (
            <button type="button" className="link" onClick={() => setDay(todayIso())}>
              Today
            </button>
          )}
        </nav>

        <button
          type="button"
          className="btn btn-primary"
          disabled={!doctors.length}
          onClick={() => setDraft({ date: day, minutes: 9 * 60 })}
        >
          Book appointment
        </button>
      </header>

      <section className="dayline">
        <h1>{longDate(day)}</h1>
        <p>{loading && !stats ? 'Loading the day…' : summary(stats, isToday)}</p>
        {stats && stats.total > 0 && (
          <div className="filters" role="group" aria-label="Show only">
            {FILTERS.filter((f) => stats[STAT_KEY[f]] > 0).map((f) => (
              <button
                key={f}
                type="button"
                aria-pressed={filter === f}
                className={`chip ${statusClass(f)}`}
                onClick={() => {
                  setFilter((cur) => (cur === f ? null : f));
                  setSelectedId(null);
                }}
              >
                {STATUSES[f].label} <b>{stats[STAT_KEY[f]]}</b>
              </button>
            ))}
          </div>
        )}
      </section>

      {error && (
        <div className="banner" role="alert">
          <strong>{error}</strong>
          <span>The board will retry every 30 seconds.</span>
          <button type="button" className="btn btn-quiet" onClick={load}>
            Retry now
          </button>
        </div>
      )}

      <main className="workspace">
        {doctors.length > 0 ? (
          <DayBoard
            doctors={doctors}
            appointments={appointments}
            load={stats?.by_doctor ?? []}
            isToday={isToday}
            filter={filter}
            selectedId={selectedId}
            onSelect={setSelectedId}
            onEmptySlot={(doctorId, minutes) => setDraft({ doctorId, date: day, minutes })}
          />
        ) : (
          <section className="board board-empty">
            <p>{loading ? 'Loading doctors…' : 'No doctors are taking bookings. Add one through the API at /docs.'}</p>
          </section>
        )}
        <SidePanel
          selected={selected}
          appointments={appointments}
          filter={filter}
          busy={busy}
          onSelect={setSelectedId}
          {...handlers}
        />
      </main>

      <footer className="footnote">
        Stats for {stats?.active_doctors ?? 0} doctors and {stats?.patients ?? 0} registered patients.{' '}
        {stats ? `${stats.upcoming_7_days} visits booked over the next 7 days.` : ''}
      </footer>

      <BookingDialog draft={draft} doctors={doctors} onClose={() => setDraft(null)} onSaved={onSaved} />

      <div className="toast" role="status" aria-live="polite" data-show={Boolean(toast)}>
        {toast}
      </div>
    </div>
  );
}
