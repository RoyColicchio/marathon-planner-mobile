import { useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { api } from '../lib/api'
import { saveSettings } from '../lib/store'

export default function StravaCallback() {
  const [params] = useSearchParams()
  const nav = useNavigate()

  useEffect(() => {
    const code = params.get('code')
    if (!code) { nav('/settings'); return }

    api.stravaExchange(code).then(tokens => {
      saveSettings({
        access_token: tokens.access_token,
        refresh_token: tokens.refresh_token,
        token_expires_at: tokens.expires_at,
        athlete: tokens.athlete,
      })
      nav('/')
    }).catch(() => {
      nav('/settings?error=auth_failed')
    })
  }, [params, nav])

  return (
    <div className="min-h-screen flex flex-col items-center justify-center">
      <div className="animate-spin w-8 h-8 border-2 border-strava border-t-transparent rounded-full mb-3"/>
      <div className="text-sm text-gray-500">Connecting to Strava...</div>
    </div>
  )
}
