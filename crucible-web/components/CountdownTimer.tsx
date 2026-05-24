'use client'

import { useEffect, useState } from 'react'

function getTimeUntilMidnight() {
  const now = new Date()
  const midnight = new Date()
  midnight.setHours(24, 0, 0, 0)
  const diff = midnight.getTime() - now.getTime()
  return {
    h: Math.floor(diff / 3_600_000),
    m: Math.floor((diff % 3_600_000) / 60_000),
    s: Math.floor((diff % 60_000) / 1_000),
  }
}

export default function CountdownTimer() {
  const [time, setTime] = useState(getTimeUntilMidnight)
  useEffect(() => {
    const id = setInterval(() => setTime(getTimeUntilMidnight()), 1000)
    return () => clearInterval(id)
  }, [])
  const isDanger = time.h === 0 && time.m < 30
  const fmt = (n: number) => String(n).padStart(2, '0')
  return (
    <div className="flex flex-col items-end">
      <p
        className={`text-lg font-bold tabular-nums tracking-widest ${
          isDanger ? 'countdown-danger' : 'text-zinc-300'
        }`}
      >
        {fmt(time.h)}:{fmt(time.m)}:{fmt(time.s)}
      </p>
      <p className="text-xs text-zinc-600 uppercase tracking-widest">until reset</p>
    </div>
  )
}
