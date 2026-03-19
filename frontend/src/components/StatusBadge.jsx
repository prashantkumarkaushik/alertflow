const STATUS_STYLES = {
  triggered: 'bg-red-900/40 text-red-400 border border-red-800',
  acknowledged: 'bg-yellow-900/40 text-yellow-400 border border-yellow-800',
  resolved: 'bg-green-900/40 text-green-400 border border-green-800',
}

const PRIORITY_STYLES = {
  P1: 'bg-red-600 text-white',
  P2: 'bg-orange-600 text-white',
  P3: 'bg-yellow-600 text-white',
  P4: 'bg-gray-600 text-white',
}

export function StatusBadge({ status }) {
  return (
    <span className={`px-2.5 py-1 rounded-full text-xs font-medium uppercase
                      ${STATUS_STYLES[status] || 'bg-gray-800 text-gray-400'}`}>
      {status}
    </span>
  )
}

export function PriorityBadge({ priority }) {
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-bold
                      ${PRIORITY_STYLES[priority] || 'bg-gray-600 text-white'}`}>
      {priority}
    </span>
  )
}

export function SLABadge({ breached, deadline, status }) {
  if (!deadline) return <span className="text-gray-600 text-xs">No SLA</span>

  // If resolved — show SLA met or breached, no countdown
  if (status === 'resolved') {
    if (breached) {
      return (
        <span className="text-red-400 text-xs font-medium flex items-center gap-1">
          <span className="w-1.5 h-1.5 bg-red-400 rounded-full inline-block" />
          SLA Breached
        </span>
      )
    }
    return (
      <span className="text-green-400 text-xs font-medium flex items-center gap-1">
        <span className="w-1.5 h-1.5 bg-green-400 rounded-full inline-block" />
        SLA Met
      </span>
    )
  }

  if (breached) {
    return (
      <span className="text-red-400 text-xs font-medium flex items-center gap-1">
        <span className="w-1.5 h-1.5 bg-red-400 rounded-full inline-block" />
        SLA Breached
      </span>
    )
  }

  const deadline_date = new Date(deadline)
  const now = new Date()
  const diff = deadline_date - now
  const hours = Math.floor(diff / 1000 / 60 / 60)
  const mins = Math.floor((diff / 1000 / 60) % 60)

  if (diff < 0) {
    return <span className="text-red-400 text-xs">Overdue</span>
  }

  return (
    <span className="text-yellow-400 text-xs">
      {hours > 0 ? `${hours}h ${mins}m` : `${mins}m`} remaining
    </span>
  )
}
