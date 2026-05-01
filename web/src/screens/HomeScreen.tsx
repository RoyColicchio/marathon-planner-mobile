import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { format, parseISO, differenceInDays, startOfWeek, addDays, isToday } from 'date-fns'
import { api, Schedule, Run, StravaActivity } from '../lib/api'
import { loadSettings, UserSettings } from '../lib/store'

const TYPE_LABEL: Record<string, string> = {
  easy: 'Easy', long: 'Long', tempo: 'Tempo', vo2: 'VO₂', race: 'Race',
  me_primary: 'Primary', me_secondary: 'Secondary', me_weekend: 'Weekend',
}

const TYPE_PILL: Record<string, string> = {
  easy: 'pill-easy', long: 'pill-long', tempo: 'pill-tempo', vo2: 'pill-vo2',
  race: 'pill-race',
  me_primary: 'pill-vo2', me_secondary: 'pill-tempo', me_weekend: 'pill-long',
}

export default function HomeScreen() {
  const [settings] = useState<UserSettings>(() => loadSettings())
  const [schedule, setSchedule] = useState<Schedule | null>(null)
  const [activities, setActivities] = useState<Record<string, StravaActivity[]>>({})
  const [loading, setLoading] = useState(true)
  const [err, setErr] = useState<string | null>(null)

  useEffect(() => {
    if (!settings.race_date) {
      setLoading(false)
      return
    }
    api.getSchedule(settings.selected_plan, {
      race_date: settings.race_date,
      long_dow: settings.long_dow,
      quality_dow: settings.quality_dow,
      rest_dow: settings.rest_dow,
    }).then(setSchedule).catch(e => setErr(String(e))).finally(() => setLoading(false))

    if (settings.access_token) {
      api.getActivities(settings.access_token).then(setActivities).catch(() => {})
    }
  }, [settings.selected_plan, settings.race_date, settings.long_dow, settings.quality_dow, settings.rest_dow])

  if (!settings.race_date) {
    return <Onboarding />
  }

  if (loading) return <Loading />
  if (err) return <ErrorState message={err} />
  if (!schedule) return <ErrorState message="No schedule available" />

  const today = new Date()
  const todayStr = format(today, 'yyyy-MM-dd')
  const raceDate = parseISO(schedule.race_date)
  const planStart = parseISO(schedule.plan_start)
  const daysToRace = differenceInDays(raceDate, today)
  const daysIn = differenceInDays(today, planStart)
  const totalDays = differenceInDays(raceDate, planStart)
  const pctComplete = Math.max(0, Math.min(100, Math.round((daysIn / totalDays) * 100)))

  const dayMap: Record<string, Run> = {}
  schedule.days.forEach(d => { dayMap[d.date] = d })

  const todayRun = dayMap[todayStr]
  const tomorrowRun = dayMap[format(addDays(today, 1), 'yyyy-MM-dd')]

  // Get this week (Mon → Sun)
  const weekStart = startOfWeek(today, { weekStartsOn: 1 })
  const weekDays: { date: string; run?: Run; actuals?: StravaActivity[] }[] = []
  for (let i = 0; i < 7; i++) {
    const d = addDays(weekStart, i)
    const ds = format(d, 'yyyy-MM-dd')
    weekDays.push({ date: ds, run: dayMap[ds], actuals: activities[ds] })
  }

  const weekTotal = weekDays.reduce((sum, d) => sum + (d.run?.m || 0), 0)
  const weekActual = weekDays.reduce(
    (sum, d) => sum + (d.actuals?.reduce((s, a) => s + a.miles, 0) || 0), 0
  )

  return (
    <div className="min-h-screen pb-24">
      {/* Top bar */}
      <header className="sticky top-0 z-10 bg-white/90 backdrop-blur border-b border-gray-100 px-4 py-3 flex items-center justify-between">
        <div>
          <div className="text-[11px] uppercase tracking-wider text-gray-400">Marathon Planner</div>
          <div className="text-base font-semibold text-gray-900">{schedule.plan.name}</div>
        </div>
        <Link to="/settings" className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center text-gray-600 active:bg-gray-200">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
        </Link>
      </header>

      {/* Race countdown card */}
      <div className="px-4 pt-4">
        <div className="rounded-2xl bg-gradient-to-br from-strava to-strava-dark text-white p-5 shadow-md">
          <div className="text-[10px] uppercase tracking-wider opacity-80">Days to race</div>
          <div className="text-5xl font-light leading-tight mt-1">{Math.max(0, daysToRace)}</div>
          <div className="text-xs opacity-80 mt-1">{format(raceDate, 'EEE · MMM d, yyyy')}</div>
        </div>
      </div>

      {/* Plan progress */}
      <div className="px-4 pt-3">
        <div className="card">
          <div className="flex justify-between items-baseline mb-2">
            <div>
              <div className="text-[10px] uppercase tracking-wider text-gray-400">Plan progress</div>
              <div className="text-base font-semibold text-gray-900">Week {Math.min(schedule.plan.weeks, Math.floor(daysIn / 7) + 1)} of {schedule.plan.weeks}</div>
            </div>
            <div className="text-xs text-strava font-semibold">{pctComplete}%</div>
          </div>
          <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
            <div className="h-full bg-gradient-to-r from-emerald-400 to-strava transition-all" style={{ width: `${pctComplete}%` }}/>
          </div>
        </div>
      </div>

      {/* Today / tomorrow card */}
      <div className="px-4 pt-3">
        <div className="card">
          <div className="text-[10px] uppercase tracking-wider text-gray-400 mb-2">
            {todayRun ? "Today's run" : tomorrowRun ? "Tomorrow's run" : "Today"}
          </div>
          {todayRun ? (
            <Link to={`/workout/${todayStr}`} className="block">
              <RunRow run={todayRun} large />
            </Link>
          ) : tomorrowRun ? (
            <Link to={`/workout/${format(addDays(today, 1), 'yyyy-MM-dd')}`} className="block">
              <RunRow run={tomorrowRun} large />
            </Link>
          ) : (
            <div className="text-gray-400 text-sm">Rest day — recover well</div>
          )}
        </div>
      </div>

      {/* This week list */}
      <div className="px-4 pt-3">
        <div className="card">
          <div className="flex justify-between items-center mb-3">
            <div className="text-[10px] uppercase tracking-wider text-gray-400">This week</div>
            <div className="text-xs text-gray-500"><span className="font-semibold text-gray-700">{weekActual.toFixed(1)}</span> done / <span className="text-gray-400">{weekTotal} planned</span></div>
          </div>
          <div className="space-y-2">
            {weekDays.map(({ date, run, actuals }) => {
              const d = parseISO(date)
              const dow = format(d, 'EEE')
              const dayNum = format(d, 'd')
              const past = date < todayStr
              const isCurrentDay = isToday(d)
              const actMiles = actuals?.reduce((s, a) => s + a.miles, 0) || 0

              return (
                <Link
                  key={date}
                  to={run ? `/workout/${date}` : '#'}
                  className={`flex items-center justify-between py-2 px-2 -mx-2 rounded-lg ${run ? 'active:bg-gray-50' : ''} ${isCurrentDay ? 'bg-strava/5' : ''}`}
                  onClick={e => { if (!run) e.preventDefault() }}
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className={`w-10 text-center ${isCurrentDay ? 'text-strava font-bold' : 'text-gray-400'}`}>
                      <div className="text-[10px] uppercase">{dow}</div>
                      <div className="text-base leading-tight">{dayNum}</div>
                    </div>
                    {run ? (
                      <div className="flex items-center gap-2 min-w-0">
                        <span className={`pill ${TYPE_PILL[run.t] || 'pill-rest'}`}>{TYPE_LABEL[run.t] || 'Run'}</span>
                        <div className="flex flex-col leading-tight">
                          <span className="text-sm text-gray-700 font-medium">{run.m}mi</span>
                          <span className="text-[10px] text-gray-400">planned</span>
                        </div>
                      </div>
                    ) : (
                      <span className="text-sm text-gray-400">Rest</span>
                    )}
                  </div>
                  <div className="text-right shrink-0">
                    {actMiles > 0 ? (
                      <div className="flex flex-col leading-tight items-end">
                        <span className={`text-sm font-semibold ${past || isCurrentDay ? 'text-emerald-600' : 'text-gray-700'}`}>
                          ✓ {actMiles.toFixed(1)}mi
                        </span>
                        <span className="text-[10px] text-gray-400">
                          {run ? `${Math.round(actMiles / run.m * 100)}% of plan` : 'unplanned'}
                        </span>
                      </div>
                    ) : run && past ? (
                      <span className="text-xs text-red-500 font-semibold">missed</span>
                    ) : null}
                  </div>
                </Link>
              )
            })}
          </div>
        </div>
      </div>

      {/* Future weeks browser */}
      <div className="px-4 pt-3">
        <FutureWeeks schedule={schedule} activities={activities} todayStr={todayStr} />
      </div>
    </div>
  )
}

function RunRow({ run, large = false }: { run: Run; large?: boolean }) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-3">
        <span className={`pill ${TYPE_PILL[run.t] || 'pill-rest'} ${large ? '!text-sm !px-3 !py-1.5' : ''}`}>{TYPE_LABEL[run.t] || 'Run'}</span>
        <div>
          <div className={`font-semibold text-gray-900 ${large ? 'text-2xl' : 'text-base'}`}>{run.m} mi</div>
          {run.note && large && <div className="text-xs text-gray-500 mt-0.5 line-clamp-2">{run.note}</div>}
        </div>
      </div>
      <svg className="text-gray-300" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="9 18 15 12 9 6"/></svg>
    </div>
  )
}

function FutureWeeks({ schedule, activities, todayStr }: { schedule: Schedule; activities: Record<string, StravaActivity[]>; todayStr: string }) {
  const dayMap: Record<string, Run> = {}
  schedule.days.forEach(d => { dayMap[d.date] = d })

  const today = parseISO(todayStr)
  const planStart = parseISO(schedule.plan_start)
  const raceDate = parseISO(schedule.race_date)
  const thisWeekStart = startOfWeek(today, { weekStartsOn: 1 })

  // Build the list of all weeks from plan_start through race week
  const allWeeks: Date[] = []
  let w = startOfWeek(planStart, { weekStartsOn: 1 })
  const end = startOfWeek(raceDate, { weekStartsOn: 1 })
  while (w <= end) {
    allWeeks.push(w)
    w = addDays(w, 7)
  }

  // Find current-week index and start the browser at next week
  const currentIdx = allWeeks.findIndex(d => d.getTime() === thisWeekStart.getTime())
  const initialOffset = currentIdx >= 0 ? currentIdx + 1 : 0

  const [offset, setOffset] = useState(initialOffset)
  const [expanded, setExpanded] = useState<string | null>(null)

  const PAGE = 4
  const visibleWeeks = allWeeks.slice(offset, offset + PAGE)
  const canGoBack = offset > 0
  const canGoForward = offset + PAGE < allWeeks.length

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-3">
        <div className="text-[10px] uppercase tracking-wider text-gray-400">Upcoming weeks</div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setOffset(Math.max(0, offset - PAGE))}
            disabled={!canGoBack}
            className={`w-8 h-8 rounded-full flex items-center justify-center ${canGoBack ? 'text-gray-700 active:bg-gray-100' : 'text-gray-300'}`}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="15 18 9 12 15 6"/></svg>
          </button>
          <button
            onClick={() => setOffset(Math.min(allWeeks.length - PAGE, offset + PAGE))}
            disabled={!canGoForward}
            className={`w-8 h-8 rounded-full flex items-center justify-center ${canGoForward ? 'text-gray-700 active:bg-gray-100' : 'text-gray-300'}`}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="9 18 15 12 9 6"/></svg>
          </button>
        </div>
      </div>
      <div className="space-y-2">
        {visibleWeeks.map(ws => (
          <WeekItem
            key={ws.toISOString()}
            weekStart={ws}
            dayMap={dayMap}
            activities={activities}
            todayStr={todayStr}
            isExpanded={expanded === ws.toISOString()}
            onToggle={() => setExpanded(expanded === ws.toISOString() ? null : ws.toISOString())}
          />
        ))}
      </div>
      {visibleWeeks.length === 0 && (
        <div className="text-sm text-gray-400 text-center py-4">No more weeks</div>
      )}
    </div>
  )
}

function WeekItem({ weekStart, dayMap, activities, todayStr, isExpanded, onToggle }: {
  weekStart: Date
  dayMap: Record<string, Run>
  activities: Record<string, StravaActivity[]>
  todayStr: string
  isExpanded: boolean
  onToggle: () => void
}) {
  const days: { date: string; run?: Run }[] = []
  for (let i = 0; i < 7; i++) {
    const ds = format(addDays(weekStart, i), 'yyyy-MM-dd')
    days.push({ date: ds, run: dayMap[ds] })
  }
  const total = days.reduce((s, d) => s + (d.run?.m || 0), 0)
  const actualTotal = days.reduce(
    (s, d) => s + (activities[d.date]?.reduce((m, a) => m + a.miles, 0) || 0), 0
  )

  // A week is "past" once its last day is before today
  const lastDayStr = format(addDays(weekStart, 6), 'yyyy-MM-dd')
  const isPast = lastDayStr < todayStr

  return (
    <div>
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between py-2 px-2 -mx-2 rounded-lg active:bg-gray-50"
      >
        <div className="flex items-center gap-2">
          <svg
            className={`text-gray-400 transition-transform ${isExpanded ? 'rotate-90' : ''}`}
            width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"
          ><polyline points="9 18 15 12 9 6"/></svg>
          <div className="text-sm text-gray-700">Week of {format(weekStart, 'MMM d')}</div>
        </div>
        {isPast ? (
          <div className="text-xs text-right">
            <span className="font-semibold text-gray-700">{actualTotal.toFixed(1)}</span>
            <span className="text-gray-400"> / {total} mi</span>
          </div>
        ) : (
          <div className="text-xs">
            <span className="text-gray-700 font-semibold">{total} mi</span>
          </div>
        )}
      </button>
      {isExpanded && (
        <div className="mt-1 mb-2 ml-6 space-y-1.5 border-l-2 border-gray-100 pl-4">
          {days.map(({ date, run }) => {
            const d = parseISO(date)
            const dow = format(d, 'EEE')
            const dayNum = format(d, 'd')
            const past = date < todayStr
            const acts = activities[date]
            const actMiles = acts?.reduce((s, a) => s + a.miles, 0) || 0

            return (
              <Link
                key={date}
                to={run ? `/workout/${date}` : '#'}
                onClick={e => { if (!run) e.preventDefault() }}
                className={`flex items-center justify-between py-1.5 px-2 -mx-2 rounded-lg ${run ? 'active:bg-gray-50' : ''}`}
              >
                <div className="flex items-center gap-3 min-w-0">
                  <div className="w-9 text-center text-gray-400">
                    <div className="text-[10px] uppercase">{dow}</div>
                    <div className="text-sm leading-tight">{dayNum}</div>
                  </div>
                  {run ? (
                    <div className="flex items-center gap-2 min-w-0">
                      <span className={`pill ${TYPE_PILL[run.t] || 'pill-rest'} !text-[10px]`}>{TYPE_LABEL[run.t] || 'Run'}</span>
                      <div className="flex flex-col leading-tight">
                        <span className="text-sm text-gray-700">{run.m}mi</span>
                        <span className="text-[9px] text-gray-400">planned</span>
                      </div>
                    </div>
                  ) : (
                    <span className="text-xs text-gray-400">Rest</span>
                  )}
                </div>
                <div className="text-right shrink-0">
                  {actMiles > 0 ? (
                    <div className="flex flex-col leading-tight items-end">
                      <span className={`text-xs font-semibold ${past ? 'text-emerald-600' : 'text-gray-700'}`}>✓ {actMiles.toFixed(1)}mi</span>
                      <span className="text-[9px] text-gray-400">{run ? 'done' : 'unplanned'}</span>
                    </div>
                  ) : run && past ? (
                    <span className="text-[10px] text-red-500 font-semibold">missed</span>
                  ) : null}
                </div>
              </Link>
            )
          })}
        </div>
      )}
    </div>
  )
}


function Onboarding() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-6 text-center">
      <div className="w-16 h-16 rounded-full bg-strava/10 flex items-center justify-center mb-4">
        <svg className="text-strava" width="32" height="32" viewBox="0 0 24 24" fill="currentColor"><path d="M15.387 17.944l-2.089-4.116h-3.065L15.387 24l5.15-10.172h-3.066m-7.008-5.599l2.836 5.598h4.172L10.463 0l-7 13.828h4.169"/></svg>
      </div>
      <h1 className="text-2xl font-bold text-gray-900 mb-2">Welcome</h1>
      <p className="text-gray-500 max-w-xs mb-6">Set your race date and goal to generate your training plan.</p>
      <Link to="/settings" className="bg-strava text-white px-6 py-3 rounded-full font-semibold active:bg-strava-dark">
        Get started
      </Link>
    </div>
  )
}

function Loading() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="animate-spin w-8 h-8 border-2 border-strava border-t-transparent rounded-full"/>
    </div>
  )
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-6 text-center">
      <div className="text-red-500 mb-2">Something went wrong</div>
      <div className="text-xs text-gray-500 max-w-md">{message}</div>
      <Link to="/settings" className="mt-4 text-strava font-semibold">Settings</Link>
    </div>
  )
}
