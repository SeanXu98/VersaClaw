import path from 'path'
import os from 'os'

/**
 * Get Nanobot home directory from environment or default to ~/.nanobot
 */
export function getNanobotHome(): string {
  return process.env.NANOBOT_HOME || path.join(os.homedir(), '.nanobot')
}

/**
 * Nanobot directory paths
 */
export const PATHS = {
  // Root directory
  home: () => getNanobotHome(),

  // Configuration
  config: () => path.join(getNanobotHome(), 'config.json'),

  // Lock file
  lock: () => path.join(getNanobotHome(), 'nanobot.lock'),

  // Sessions
  sessionsDir: () => path.join(getNanobotHome(), 'sessions'),
  session: (filename: string) => path.join(getNanobotHome(), 'sessions', filename),

  // Workspace
  workspaceDir: () => path.join(getNanobotHome(), 'workspace'),

  // Memory
  memoryDir: () => path.join(getNanobotHome(), 'workspace', 'memory'),
  longTermMemory: () => path.join(getNanobotHome(), 'workspace', 'memory', 'MEMORY.md'),
  historyLog: () => path.join(getNanobotHome(), 'workspace', 'memory', 'HISTORY.md'),
  heartbeat: () => path.join(getNanobotHome(), 'workspace', 'HEARTBEAT.md'),

  // Skills
  skillsDir: () => path.join(getNanobotHome(), 'workspace', 'skills'),
  skill: (skillName: string) => path.join(getNanobotHome(), 'workspace', 'skills', skillName, 'SKILL.md'),

  // Cron
  cron: () => path.join(getNanobotHome(), 'workspace', '.cron.json'),
} as const

// Export convenience function for lock file
export function NANOBOT_LOCK_FILE(): string {
  return path.join(getNanobotHome(), 'nanobot.lock')
}

/**
 * Validate that a path is within the Nanobot home directory (security)
 */
export function validatePath(filePath: string): boolean {
  const normalized = path.resolve(filePath)
  const home = path.resolve(getNanobotHome())
  return normalized.startsWith(home)
}
