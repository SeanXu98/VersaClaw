import fs from 'fs/promises'
import { PATHS, validatePath } from './paths'
import type { NanobotConfig } from '@/types/nanobot'

/**
 * Convert camelCase object keys to snake_case for Python compatibility
 */
function camelToSnake(obj: any): any {
  if (obj === null || typeof obj !== 'object') {
    return obj
  }

  if (Array.isArray(obj)) {
    return obj.map(camelToSnake)
  }

  return Object.keys(obj).reduce((acc: any, key: string) => {
    // Only convert if key starts with lowercase (camelCase/PascalCase)
    // Skip keys that are already snake_case or have special characters (like HTTP headers)
    if (/^[a-z]/.test(key) && key.includes('_') === false) {
      const snakeKey = key.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`)
      acc[snakeKey] = camelToSnake(obj[key])
    } else {
      // Keep the key as-is for already snake_case or special keys
      acc[key] = camelToSnake(obj[key])
    }
    return acc
  }, {})
}

/**
 * Convert snake_case object keys to camelCase for TypeScript
 */
function snakeToCamel(obj: any): any {
  if (obj === null || typeof obj !== 'object') {
    return obj
  }

  if (Array.isArray(obj)) {
    return obj.map(snakeToCamel)
  }

  return Object.keys(obj).reduce((acc: any, key: string) => {
    const camelKey = key.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase())
    acc[camelKey] = snakeToCamel(obj[key])
    return acc
  }, {})
}

/**
 * Read Nanobot config.json
 * Converts snake_case keys to camelCase for TypeScript
 */
export async function readConfig(): Promise<NanobotConfig> {
  const configPath = PATHS.config()

  if (!validatePath(configPath)) {
    throw new Error('Invalid config path - path traversal detected')
  }

  try {
    const content = await fs.readFile(configPath, 'utf-8')
    const parsed = JSON.parse(content)
    return snakeToCamel(parsed) as NanobotConfig
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === 'ENOENT') {
      // Return empty config if file doesn't exist
      return {}
    }
    throw new Error(`Failed to read config: ${(error as Error).message}`)
  }
}

/**
 * Write Nanobot config.json with atomic write
 * Converts camelCase keys to snake_case for Python compatibility
 */
export async function writeConfig(config: NanobotConfig): Promise<void> {
  const configPath = PATHS.config()

  if (!validatePath(configPath)) {
    throw new Error('Invalid config path - path traversal detected')
  }

  try {
    // Convert camelCase to snake_case for Python backend compatibility
    const snakeCaseConfig = camelToSnake(config)

    // Atomic write: write to temp file, then rename
    const tempPath = `${configPath}.tmp`
    await fs.writeFile(tempPath, JSON.stringify(snakeCaseConfig, null, 2), 'utf-8')
    await fs.rename(tempPath, configPath)
  } catch (error) {
    throw new Error(`Failed to write config: ${(error as Error).message}`)
  }
}

/**
 * Update specific fields in config
 */
export async function updateConfig(updates: Partial<NanobotConfig>): Promise<void> {
  const current = await readConfig()
  const updated = { ...current, ...updates }
  await writeConfig(updated)
}
