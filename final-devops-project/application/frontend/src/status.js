export const STATUSES = {
  SCHEDULED: { label: 'Expected', verb: null },
  CHECKED_IN: { label: 'Waiting', verb: 'Check in' },
  COMPLETED: { label: 'Seen', verb: 'Mark as seen' },
  NO_SHOW: { label: 'Did not arrive', verb: 'Mark did not arrive' },
  CANCELLED: { label: 'Cancelled', verb: 'Cancel appointment' },
};

// Which front-desk actions make sense from each state.
export const NEXT_ACTIONS = {
  SCHEDULED: ['CHECKED_IN', 'NO_SHOW', 'CANCELLED'],
  CHECKED_IN: ['COMPLETED', 'SCHEDULED'],
  COMPLETED: ['CHECKED_IN'],
  NO_SHOW: ['SCHEDULED', 'CHECKED_IN'],
  CANCELLED: [],
};

export const statusClass = (s) => `st-${s.toLowerCase().replace('_', '-')}`;
