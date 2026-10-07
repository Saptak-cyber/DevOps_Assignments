import { useEffect, useRef } from 'react';
import { DAY_END, DAY_START, clock, formatDuration, hhmm, minutesOf, nowMinutes } from '../time.js';
import { STATUSES, statusClass } from '../status.js';

const PX_PER_MIN = 2;
const HOURS = Array.from({ length: (DAY_END - DAY_START) / 60 + 1 }, (_, i) => DAY_START + i * 60);
const top = (minutes) => (minutes - DAY_START) * PX_PER_MIN;

export default function DayBoard({ doctors, appointments, load, isToday, filter, selectedId, onSelect, onEmptySlot }) {
  const scroller = useRef(null);
  const now = nowMinutes();
  const showNow = isToday && now >= DAY_START && now <= DAY_END;

  // Open the board around the current time (today) or the first booking (other days).
  useEffect(() => {
    const el = scroller.current;
    if (!el) return;
    const first = appointments.length ? Math.min(...appointments.map((a) => minutesOf(a.scheduled_at))) : DAY_START;
    const anchor = showNow ? now - 60 : first - 30;
    el.scrollTop = Math.max(0, top(anchor));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [doctors.length, isToday]);

  const loadFor = (id) => load.find((l) => l.doctor_id === id);

  function handleColumnClick(event, doctor) {
    if (event.target !== event.currentTarget) return;
    const y = event.nativeEvent.offsetY;
    const minutes = Math.round((DAY_START + y / PX_PER_MIN) / 15) * 15;
    onEmptySlot(doctor.id, Math.min(Math.max(minutes, DAY_START), DAY_END - 15));
  }

  return (
    <section className="board" aria-label="Appointments by doctor">
      <div className="board-scroll" ref={scroller}>
        <div className="board-grid" style={{ '--cols': doctors.length }}>
          <div className="board-corner" />
          {doctors.map((d) => {
            const l = loadFor(d.id);
            return (
              <header key={d.id} className="doc-head">
                <strong>{d.full_name}</strong>
                <span>{d.specialty}</span>
                <span className="doc-load" title={l?.booked ? `${formatDuration(l.booked_minutes)} booked` : undefined}>
                  Room {d.room}, {l?.booked ? `${l.booked} booked` : 'nothing booked'}
                </span>
              </header>
            );
          })}

          <div className="ruler" style={{ height: top(DAY_END) }}>
            {HOURS.map((h) => (
              <span key={h} style={{ top: top(h) }}>
                {hhmm(h)}
              </span>
            ))}
          </div>

          {doctors.map((d) => (
            <div
              key={d.id}
              className="lane"
              style={{ height: top(DAY_END), '--hour': `${60 * PX_PER_MIN}px` }}
              onClick={(e) => handleColumnClick(e, d)}
              title={`Click an empty space to book with ${d.full_name}`}
            >
              {appointments
                .filter((a) => a.doctor.id === d.id)
                .map((a) => {
                  const start = minutesOf(a.scheduled_at);
                  const compact = a.duration_minutes < 25;
                  return (
                    <button
                      key={a.id}
                      type="button"
                      className={`slot ${statusClass(a.status)} ${selectedId === a.id ? 'is-selected' : ''} ${compact ? 'is-compact' : ''} ${filter && filter !== a.status ? 'is-dimmed' : ''}`}
                      style={{ top: top(start), height: Math.max(a.duration_minutes * PX_PER_MIN - 3, 18) }}
                      onClick={() => onSelect(a.id)}
                      aria-label={`${clock(a.scheduled_at)} ${a.patient.full_name}, ${STATUSES[a.status].label}`}
                    >
                      <span className="slot-time">{clock(a.scheduled_at)}</span>
                      <span className="slot-name">{a.patient.full_name}</span>
                      {a.duration_minutes >= 40 && <span className="slot-reason">{a.reason || STATUSES[a.status].label}</span>}
                    </button>
                  );
                })}
            </div>
          ))}

          {showNow && (
            <div className="now-line" style={{ top: `calc(var(--head-h) + ${top(now)}px)` }} aria-hidden="true">
              <span>{hhmm(now)}</span>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
