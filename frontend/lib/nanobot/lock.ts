import * as lockfile from 'proper-lockfile'

/**
 * Acquire a lock on a file
 */
export async function acquireLock(filePath: string): Promise<() => Promise<void>> {
  try {
    const release = await lockfile.lock(filePath, {
      retries: {
        retries: 5,
        minTimeout: 100,
        maxTimeout: 1000,
      },
      stale: 10000, // Consider lock stale after 10 seconds
    })
    return release
  } catch (error) {
    throw new Error(`Failed to acquire lock for ${filePath}: ${(error as Error).message}`)
  }
}

/**
 * Execute a function with file lock
 */
export async function withLock<T>(
  filePath: string,
  fn: () => Promise<T>
): Promise<T> {
  const release = await acquireLock(filePath)
  try {
    return await fn()
  } finally {
    await release()
  }
}

/**
 * Check if a file is locked
 */
export async function isLocked(filePath: string): Promise<boolean> {
  try {
    return await lockfile.check(filePath)
  } catch {
    return false
  }
}
