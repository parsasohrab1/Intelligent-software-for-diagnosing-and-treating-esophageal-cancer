import { useState, useCallback, useRef } from 'react'
import api from '../services/api'

export type JobStatus = 'pending' | 'running' | 'done' | 'failed'

export interface JobRecord {
  job_id: string
  type: string
  status: JobStatus
  result?: Record<string, unknown>
  error?: string
  created_at?: string
  updated_at?: string
}

export function useJobPolling() {
  const [job, setJob] = useState<JobRecord | null>(null)
  const [polling, setPolling] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
    setPolling(false)
  }, [])

  const pollJob = useCallback(
    async (jobId: string): Promise<JobRecord> => {
      const response = await api.get<JobRecord>(`/jobs/${jobId}`)
      setJob(response.data)
      return response.data
    },
    []
  )

  const submitJob = useCallback(
    async (type: string, params: Record<string, unknown> = {}) => {
      setError(null)
      setJob(null)
      stopPolling()

      try {
        const response = await api.post<JobRecord>('/jobs', { type, params })
        const { job_id } = response.data
        setJob(response.data)
        setPolling(true)

        return new Promise<JobRecord>((resolve, reject) => {
          intervalRef.current = setInterval(async () => {
            try {
              const record = await pollJob(job_id)
              if (record.status === 'done' || record.status === 'failed') {
                stopPolling()
                if (record.status === 'failed') {
                  setError(record.error || 'Job failed')
                  reject(new Error(record.error || 'Job failed'))
                } else {
                  resolve(record)
                }
              }
            } catch (err) {
              stopPolling()
              const msg = err instanceof Error ? err.message : 'Polling failed'
              setError(msg)
              reject(err)
            }
          }, 1500)
        })
      } catch (err: unknown) {
        const msg =
          (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
          (err instanceof Error ? err.message : 'Failed to submit job')
        setError(msg)
        throw err
      }
    },
    [pollJob, stopPolling]
  )

  return { job, polling, error, submitJob, stopPolling }
}
