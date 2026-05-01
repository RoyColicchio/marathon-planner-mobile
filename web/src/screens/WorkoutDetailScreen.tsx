import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { format, parseISO } from 'date-fns'
import { api, WorkoutDetail, Schedule, Run } from '../lib/api'
import { loadSettings } from '../lib/store'

export default function WorkoutDetailScreen() {
  const { date } = useParams<{ date: string }>()
  const [run, setRun] = useState<Run | null>(null)
  const [detail, setDetail] = useState<WorkoutDetail | null>(null)
  const [err, setErr] = useState<string | null>(null)

  useEffect(() => {
    if (!date) return
    const settings = loadSettings()
    if (!settings.race_date) return

    api.getSchedule(settings.selected_plan, {
      race_date: settings.race_date,
      long_dow: settings.long_dow,
      quality_dow: settings.quality_dow,
      rest_dow: settings.rest_dow,
    }).then(sched => {
      const found = sched.days.find(d => d.date === date)
      if (!found) { setErr('Workout not found'); return }
      setRun(found)
      return api.workoutDetail({
        workout_type: found.t,
        miles: found.m,
        goal_time: settings.goal_time,
        note: found.note,
      })
    }).then(d => { if (d) setDetail(d) }).catch(e => setErr(String(e)))
  }, [date])

  if (err) return <ErrorPanel message={err}/>
  if (!run || !detail) return <Loading/>

  const dateObj = parseISO(date!)

  return (
    <div className="min-h-screen pb-24">
      <header className="sticky top-0 z-10 bg-white/90 backdrop-blur border-b border-gray-100 px-4 py-3 flex items-center gap-3">
        <Link to="/" className="text-strava font-semibold">← Back</Link>
        <div className="text-base font-semibold text-gray-900">{format(dateObj, 'EEE, MMM d')}</div>
      </header>

      <div className="px-4 py-4 space-y-4">
        {/* Headline card */}
        <div className="card text-center">
          <div className="text-[10px] uppercase tracking-wider text-gray-400 mb-2">{labelFor(run.t)}</div>
          <div className="text-5xl font-light text-gray-900">{run.m}<span className="text-2xl text-gray-500 ml-1">mi</span></div>
          {run.note && (
            <div className="mt-3 text-sm text-gray-600 leading-relaxed">{run.note}</div>
          )}
        </div>

        {/* Pace reference */}
        <div className="card">
          <div className="text-[10px] uppercase tracking-wider text-gray-400 mb-2">Your paces</div>
          <div className="grid grid-cols-2 gap-3">
            <PaceItem label="Marathon pace" pace={fmtPace(detail.marathon_pace_secs)}/>
            <PaceItem label="5K pace (est.)" pace={fmtPace(detail.fivek_pace_secs)}/>
          </div>
        </div>

        {/* Workout structure */}
        <div className="card">
          <div className="text-[10px] uppercase tracking-wider text-gray-400 mb-3">Workout structure</div>
          <div className="space-y-3">
            {detail.segments.map((s, i) => (
              <SegmentRow key={i} segment={s}/>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

function SegmentRow({ segment }: { segment: { label: string; distance: string; pace: string; detail: string } }) {
  return (
    <div className="border-l-2 border-strava/30 pl-3 py-1">
      <div className="flex items-baseline justify-between gap-2">
        <div className="font-semibold text-sm text-gray-900 flex-1">{segment.label}</div>
        <div className="font-mono text-xs text-gray-700 shrink-0">{segment.distance}</div>
      </div>
      {segment.pace && segment.pace !== '—' && (
        <div className="text-xs font-mono text-strava font-semibold mt-0.5">{segment.pace}</div>
      )}
      {segment.detail && (
        <div className="text-xs text-gray-600 mt-1 leading-relaxed">{segment.detail}</div>
      )}
    </div>
  )
}

function PaceItem({ label, pace }: { label: string; pace: string }) {
  return (
    <div>
      <div className="text-[10px] uppercase tracking-wider text-gray-400">{label}</div>
      <div className="text-base font-mono font-semibold text-gray-900">{pace}/mi</div>
    </div>
  )
}

function fmtPace(secs: number) {
  const m = Math.floor(secs / 60)
  const s = Math.round(secs % 60).toString().padStart(2, '0')
  return `${m}:${s}`
}

function labelFor(t: string) {
  return ({
    easy: 'Easy run', long: 'Long run', tempo: 'Lactate threshold', vo2: 'VO₂ max',
    race: 'Race day',
    me_primary: 'Primary workout', me_secondary: 'Secondary workout', me_weekend: 'Weekend workout',
  } as Record<string, string>)[t] || 'Run'
}

function Loading() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="animate-spin w-8 h-8 border-2 border-strava border-t-transparent rounded-full"/>
    </div>
  )
}

function ErrorPanel({ message }: { message: string }) {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-6 text-center">
      <div className="text-red-500 mb-2">{message}</div>
      <Link to="/" className="text-strava font-semibold mt-4">Back to home</Link>
    </div>
  )
}
