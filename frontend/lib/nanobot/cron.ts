import fs from 'fs/promises'
import { PATHS, validatePath } from './paths'
import type { CronJob, CronStore } from '@/types/nanobot'

/**
 * Read cron jobs
 */
export async function readCronJobs(): Promise<CronJob[]> {
  const cronPath = PATHS.cron()

  if (!validatePath(cronPath)) {
    throw new Error('Invalid cron path - path traversal detected')
  }

  try {
    const content = await fs.readFile(cronPath, 'utf-8')
    const store = JSON.parse(content) as CronStore
    return store.jobs || []
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === 'ENOENT') {
      // Return empty array if file doesn't exist
      return []
    }
    throw new Error(`Failed to read cron jobs: ${(error as Error).message}`)
  }
}

/**
 * Write cron jobs (atomic write)
 */
export async function writeCronJobs(jobs: CronJob[]): Promise<void> {
  const cronPath = PATHS.cron()

  if (!validatePath(cronPath)) {
    throw new Error('Invalid cron path - path traversal detected')
  }

  try {
    // Ensure workspace directory exists
    await fs.mkdir(PATHS.workspaceDir(), { recursive: true })

    const store: CronStore = { jobs }

    // Atomic write
    const tempPath = `${cronPath}.tmp`
    await fs.writeFile(tempPath, JSON.stringify(store, null, 2), 'utf-8')
    await fs.rename(tempPath, cronPath)
  } catch (error) {
    throw new Error(`Failed to write cron jobs: ${(error as Error).message}`)
  }
}

/**
 * Get a single cron job by ID
 */
export async function getCronJob(id: string): Promise<CronJob | null> {
  const jobs = await readCronJobs()
  return jobs.find(job => job.id === id) || null
}

/**
 * Add a new cron job
 */
export async function addCronJob(job: Omit<CronJob, 'id' | 'created_at'>): Promise<CronJob> {
  const jobs = await readCronJobs()

  const newJob: CronJob = {
    ...job,
    id: generateJobId(),
    created_at: Date.now(),
  }

  jobs.push(newJob)
  await writeCronJobs(jobs)

  return newJob
}

/**
 * Update a cron job
 */
export async function updateCronJob(id: string, updates: Partial<CronJob>): Promise<void> {
  const jobs = await readCronJobs()
  const index = jobs.findIndex(job => job.id === id)

  if (index === -1) {
    throw new Error(`Cron job not found: ${id}`)
  }

  jobs[index] = { ...jobs[index], ...updates }
  await writeCronJobs(jobs)
}

/**
 * Delete a cron job
 */
export async function deleteCronJob(id: string): Promise<void> {
  const jobs = await readCronJobs()
  const filtered = jobs.filter(job => job.id !== id)

  if (filtered.length === jobs.length) {
    throw new Error(`Cron job not found: ${id}`)
  }

  await writeCronJobs(filtered)
}

/**
 * Generate a unique job ID
 */
function generateJobId(): string {
  return `job_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`
}
