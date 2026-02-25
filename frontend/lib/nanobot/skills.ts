import fs from 'fs/promises'
import path from 'path'
import { PATHS, validatePath } from './paths'
import type { SkillMetadata, SkillFrontmatter, SkillFile, SkillInfo } from '@/types/nanobot'

/**
 * Parse frontmatter from SKILL.md content
 */
function parseFrontmatter(content: string): { frontmatter: SkillFrontmatter; body: string } {
  const frontmatterRegex = /^---\n([\s\S]*?)\n---\n([\s\S]*)$/
  const match = content.match(frontmatterRegex)

  if (!match) {
    throw new Error('Invalid SKILL.md format - no frontmatter found')
  }

  const frontmatterText = match[1]
  const body = match[2]

  // Parse frontmatter (simple key: value parsing)
  const frontmatter: any = {}
  const lines = frontmatterText.split('\n')

  for (const line of lines) {
    const colonIndex = line.indexOf(':')
    if (colonIndex === -1) continue

    const key = line.slice(0, colonIndex).trim()
    let value: any = line.slice(colonIndex + 1).trim()

    // Parse boolean
    if (value === 'true') value = true
    else if (value === 'false') value = false
    // Remove quotes
    else if (value.startsWith('"') && value.endsWith('"')) {
      value = value.slice(1, -1)
    }

    frontmatter[key] = value
  }

  return {
    frontmatter: frontmatter as SkillFrontmatter,
    body
  }
}

/**
 * Generate SKILL.md content from frontmatter and body
 */
function generateSkillContent(frontmatter: SkillFrontmatter, body: string): string {
  const lines = [
    '---',
    `name: "${frontmatter.name}"`,
    `description: "${frontmatter.description}"`,
    `always: ${frontmatter.always}`,
  ]

  if (frontmatter.metadata) {
    lines.push(`metadata: ${frontmatter.metadata}`)
  }

  lines.push('---', '', body)

  return lines.join('\n')
}

/**
 * List all skills (both built-in and custom)
 */
export async function listSkills(): Promise<SkillInfo[]> {
  const skillsDir = PATHS.skillsDir()
  const skills: SkillInfo[] = []

  try {
    const entries = await fs.readdir(skillsDir, { withFileTypes: true })

    for (const entry of entries) {
      if (!entry.isDirectory()) continue

      try {
        const skillPath = path.join(skillsDir, entry.name, 'SKILL.md')
        const content = await fs.readFile(skillPath, 'utf-8')
        const { frontmatter } = parseFrontmatter(content)

        let metadata: SkillMetadata | undefined
        if (frontmatter.metadata) {
          try {
            metadata = JSON.parse(frontmatter.metadata)
          } catch {
            // Invalid JSON, ignore
          }
        }

        skills.push({
          name: entry.name,
          frontmatter,
          metadata,
          isBuiltIn: false, // We'll determine this from the nanobot source
        })
      } catch (error) {
        console.error(`Error reading skill ${entry.name}:`, error)
        continue
      }
    }

    return skills
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === 'ENOENT') {
      return []
    }
    throw new Error(`Failed to list skills: ${(error as Error).message}`)
  }
}

/**
 * Read a single skill
 */
export async function readSkill(skillName: string): Promise<SkillFile> {
  const skillPath = PATHS.skill(skillName)

  if (!validatePath(skillPath)) {
    throw new Error('Invalid skill path - path traversal detected')
  }

  try {
    const content = await fs.readFile(skillPath, 'utf-8')
    const { frontmatter, body } = parseFrontmatter(content)

    return {
      frontmatter,
      content: body
    }
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === 'ENOENT') {
      throw new Error(`Skill not found: ${skillName}`)
    }
    throw new Error(`Failed to read skill: ${(error as Error).message}`)
  }
}

/**
 * Write a skill (atomic write)
 */
export async function writeSkill(
  skillName: string,
  frontmatter: SkillFrontmatter,
  content: string
): Promise<void> {
  const skillPath = PATHS.skill(skillName)

  if (!validatePath(skillPath)) {
    throw new Error('Invalid skill path - path traversal detected')
  }

  try {
    // Ensure skill directory exists
    const skillDir = path.dirname(skillPath)
    await fs.mkdir(skillDir, { recursive: true })

    // Generate content
    const fileContent = generateSkillContent(frontmatter, content)

    // Atomic write
    const tempPath = `${skillPath}.tmp`
    await fs.writeFile(tempPath, fileContent, 'utf-8')
    await fs.rename(tempPath, skillPath)
  } catch (error) {
    throw new Error(`Failed to write skill: ${(error as Error).message}`)
  }
}

/**
 * Delete a skill
 */
export async function deleteSkill(skillName: string): Promise<void> {
  const skillPath = PATHS.skill(skillName)

  if (!validatePath(skillPath)) {
    throw new Error('Invalid skill path - path traversal detected')
  }

  try {
    const skillDir = path.dirname(skillPath)
    await fs.rm(skillDir, { recursive: true, force: true })
  } catch (error) {
    throw new Error(`Failed to delete skill: ${(error as Error).message}`)
  }
}
