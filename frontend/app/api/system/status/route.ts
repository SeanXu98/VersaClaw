import { NextResponse } from 'next/server'
import { readConfig } from '@/lib/nanobot/config'
import { listSessions } from '@/lib/nanobot/sessions'
import { exec } from 'child_process'
import { promisify } from 'util'
import type { SystemStatus } from '@/types/nanobot'
import { isLocked } from '@/lib/nanobot/lock'
import { NANOBOT_LOCK_FILE } from '@/lib/nanobot/paths'

const execAsync = promisify(exec)

/**
 * GET /api/system/status
 * 获取系统运行状态
 */
export async function GET() {
  try {
    // 并行获取所有状态信息
    const [
      isNanobotRunning,
      config,
      sessions
    ] = await Promise.all([
      checkNanobotProcess(),
      readConfig().catch(() => ({})),
      listSessions().catch(() => [])
    ])

    // 统计启用的渠道数量
    const enabledChannels = config.channels
      ? Object.values(config.channels).filter((ch: any) => ch?.enabled === true).length
      : 0

    // 统计配置的提供商数量
    const configuredProviders = config.providers
      ? Object.keys(config.providers).length
      : 0

    // 构建状态响应
    const status: SystemStatus = {
      nanobot_running: isNanobotRunning,
      enabled_channels: enabledChannels,
      configured_providers: configuredProviders,
      total_sessions: sessions.length,
      uptime: isNanobotRunning ? await getNanobotUptime() : undefined
    }

    return NextResponse.json({ data: status, success: true })
  } catch (error) {
    console.error('Failed to get system status:', error)
    return NextResponse.json(
      {
        error: 'Failed to retrieve system status',
        details: (error as Error).message
      },
      { status: 500 }
    )
  }
}

/**
 * 检查Nanobot进程是否运行
 */
async function checkNanobotProcess(): Promise<boolean> {
  const platform = process.platform

  try {
    // 优先使用锁文件检测（最可靠）
    const locked = await isLocked(NANOBOT_LOCK_FILE())
    if (locked) {
      return true
    }

    // 如果锁文件检测失败，尝试进程检测
    if (platform === 'win32') {
      // Windows: 使用 wmic 查找包含 nanobot 的 Python 进程
      const { stdout } = await execAsync('wmic process where "name=\'python.exe\' and commandline like \'%nanobot%\'" get ProcessId 2>nul')
      return stdout.includes('ProcessId') && !stdout.includes('No Instance(s) Available')
    } else {
      // Linux/Mac: 使用 pgrep 查找 nanobot 进程
      const { stdout } = await execAsync('pgrep -f "nanobot" || true')
      const pids = stdout.trim().split('\n').filter(Boolean)
      return pids.length > 0
    }
  } catch (error) {
    // 失败时返回 false
    return false
  }
}

/**
 * 获取Nanobot进程运行时间（秒）
 */
async function getNanobotUptime(): Promise<number | undefined> {
  const platform = process.platform

  try {
    if (platform === 'win32') {
      // Windows: 获取进程启动时间
      const { stdout } = await execAsync(
        'wmic process where "name=\'python.exe\' and commandline like \'%nanobot%\'" get CreationDate /value 2>nul'
      )
      const match = stdout.match(/CreationDate=([\d.]+)/)
      if (match) {
        const creationDate = new Date(match[1])
        const now = Date.now()
        return Math.floor((now - creationDate.getTime()) / 1000)
      }
    } else {
      // Linux/Mac: 获取进程PID和启动时间
      const { stdout: pidsOutput } = await execAsync('pgrep -f "nanobot" | head -1 || true')
      const pid = pidsOutput.trim()

      if (!pid) return undefined

      // 获取进程启动时间
      const { stdout: startTime } = await execAsync(`ps -p ${pid} -o lstart=`)
      const processStartTime = new Date(startTime.trim()).getTime()
      const now = Date.now()

      // 计算运行时间（秒）
      return Math.floor((now - processStartTime) / 1000)
    }
  } catch (error) {
    return undefined
  }
}
