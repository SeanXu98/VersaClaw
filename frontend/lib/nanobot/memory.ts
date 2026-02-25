import fs from 'fs/promises'
import { PATHS, validatePath } from './paths'
import type { MemoryType } from '@/types/nanobot'

/**
 * Get the path for a specific memory type
 */
function getMemoryPath(type: MemoryType): string {
  switch (type) {
    case 'longTerm':
      return PATHS.longTermMemory()
    case 'history':
      return PATHS.historyLog()
    case 'heartbeat':
      return PATHS.heartbeat()
  }
}

/**
 * Read a memory file
 */
export async function readMemory(type: MemoryType): Promise<string> {
  const filePath = getMemoryPath(type)

  if (!validatePath(filePath)) {
    throw new Error('Invalid memory path - path traversal detected')
  }

  try {
    return await fs.readFile(filePath, 'utf-8')
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === 'ENOENT') {
      // Return empty string if file doesn't exist
      return ''
    }
    throw new Error(`Failed to read memory (${type}): ${(error as Error).message}`)
  }
}

/**
 * Write a memory file (atomic write)
 */
export async function writeMemory(type: MemoryType, content: string): Promise<void> {
  const filePath = getMemoryPath(type)

  if (!validatePath(filePath)) {
    throw new Error('Invalid memory path - path traversal detected')
  }

  try {
    // Ensure memory directory exists
    await fs.mkdir(PATHS.memoryDir(), { recursive: true })

    // Atomic write
    const tempPath = `${filePath}.tmp`
    await fs.writeFile(tempPath, content, 'utf-8')
    await fs.rename(tempPath, filePath)
  } catch (error) {
    throw new Error(`Failed to write memory (${type}): ${(error as Error).message}`)
  }
}

/**
 * Search history log with grep-like functionality
 */
export async function searchHistory(query: string): Promise<string[]> {
  const history = await readMemory('history')
  const lines = history.split('\n')

  // Simple case-insensitive search
  const regex = new RegExp(query, 'i')
  return lines.filter(line => regex.test(line))
}

/**
 * Append to history log
 */
export async function appendHistory(entry: string): Promise<void> {
  const currentHistory = await readMemory('history')
  const timestamp = new Date().toISOString()
  const newEntry = `\n[${timestamp}] ${entry}`

  await writeMemory('history', currentHistory + newEntry)
}
