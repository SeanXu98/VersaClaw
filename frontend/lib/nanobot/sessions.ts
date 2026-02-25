import fs from 'fs/promises'
import path from 'path'
import { PATHS, validatePath } from './paths'
import type { SessionMessage, SessionMetadata, SessionInfo, SessionData } from '@/types/nanobot'

/**
 * Parse session key from filename (e.g., "web_user123.jsonl" -> "web:user123")
 */
export function parseSessionKey(filename: string): string {
  const base = filename.replace(/\.jsonl$/, '')
  return base.replace('_', ':')
}

/**
 * Generate filename from session key (e.g., "web:user123" -> "web_user123.jsonl")
 */
export function sessionKeyToFilename(sessionKey: string): string {
  return sessionKey.replace(':', '_') + '.jsonl'
}

/**
 * List all sessions
 */
export async function listSessions(): Promise<SessionInfo[]> {
  const sessionsDir = PATHS.sessionsDir()

  try {
    const files = await fs.readdir(sessionsDir)
    const sessions: SessionInfo[] = []

    for (const file of files) {
      if (!file.endsWith('.jsonl')) continue

      try {
        const filePath = path.join(sessionsDir, file)
        const content = await fs.readFile(filePath, 'utf-8')
        const lines = content.split('\n').filter(line => line.trim())

        if (lines.length === 0) continue

        // First line is always metadata
        const metadata = JSON.parse(lines[0]) as SessionMetadata
        const messageCount = lines.length - 1 // Subtract metadata line

        sessions.push({
          key: parseSessionKey(file),
          filename: file,
          metadata,
          messageCount,
        })
      } catch (error) {
        console.error(`Error reading session ${file}:`, error)
        continue
      }
    }

    // Sort by updated_at descending
    sessions.sort((a, b) => {
      return new Date(b.metadata.updated_at).getTime() - new Date(a.metadata.updated_at).getTime()
    })

    return sessions
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === 'ENOENT') {
      // Sessions directory doesn't exist yet
      return []
    }
    throw new Error(`Failed to list sessions: ${(error as Error).message}`)
  }
}

/**
 * Read a single session
 */
export async function readSession(sessionKey: string): Promise<SessionData> {
  const filename = sessionKeyToFilename(sessionKey)
  const filePath = PATHS.session(filename)

  if (!validatePath(filePath)) {
    throw new Error('Invalid session path - path traversal detected')
  }

  try {
    const content = await fs.readFile(filePath, 'utf-8')
    const lines = content.split('\n').filter(line => line.trim())

    if (lines.length === 0) {
      throw new Error('Empty session file')
    }

    const metadata = JSON.parse(lines[0]) as SessionMetadata
    const messages = lines.slice(1).map(line => JSON.parse(line) as SessionMessage)

    return { metadata, messages }
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === 'ENOENT') {
      throw new Error(`Session not found: ${sessionKey}`)
    }
    throw new Error(`Failed to read session: ${(error as Error).message}`)
  }
}

/**
 * Write a session (atomic write)
 */
export async function writeSession(
  sessionKey: string,
  metadata: SessionMetadata,
  messages: SessionMessage[]
): Promise<void> {
  const filename = sessionKeyToFilename(sessionKey)
  const filePath = PATHS.session(filename)

  if (!validatePath(filePath)) {
    throw new Error('Invalid session path - path traversal detected')
  }

  try {
    // Ensure sessions directory exists
    await fs.mkdir(PATHS.sessionsDir(), { recursive: true })

    // Build JSONL content
    const lines = [
      JSON.stringify(metadata),
      ...messages.map(msg => JSON.stringify(msg))
    ]
    const content = lines.join('\n') + '\n'

    // Atomic write
    const tempPath = `${filePath}.tmp`
    await fs.writeFile(tempPath, content, 'utf-8')
    await fs.rename(tempPath, filePath)
  } catch (error) {
    throw new Error(`Failed to write session: ${(error as Error).message}`)
  }
}

/**
 * Delete a session
 */
export async function deleteSession(sessionKey: string): Promise<void> {
  const filename = sessionKeyToFilename(sessionKey)
  const filePath = PATHS.session(filename)

  if (!validatePath(filePath)) {
    throw new Error('Invalid session path - path traversal detected')
  }

  try {
    await fs.unlink(filePath)
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === 'ENOENT') {
      // Already deleted
      return
    }
    throw new Error(`Failed to delete session: ${(error as Error).message}`)
  }
}
