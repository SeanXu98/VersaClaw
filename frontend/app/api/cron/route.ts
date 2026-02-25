import { NextRequest, NextResponse } from 'next/server'
import { readCronJobs, addCronJob } from '@/lib/nanobot/cron'
import type { CronJob } from '@/types/nanobot'

/**
 * GET /api/cron
 * 获取所有定时任务
 */
export async function GET() {
  try {
    const jobs = await readCronJobs()

    // 统计
    const enabled = jobs.filter(j => j.enabled).length
    const disabled = jobs.filter(j => !j.enabled).length

    return NextResponse.json({
      data: {
        jobs,
        total: jobs.length,
        enabled,
        disabled
      },
      success: true
    })
  } catch (error) {
    console.error('Failed to read cron jobs:', error)
    return NextResponse.json(
      {
        error: 'Failed to retrieve cron jobs',
        details: (error as Error).message
      },
      { status: 500 }
    )
  }
}

/**
 * POST /api/cron
 * 创建新的定时任务
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json()

    // 验证必填字段
    if (!body.name || !body.schedule || !body.payload) {
      return NextResponse.json(
        { error: 'Missing required fields: name, schedule, payload' },
        { status: 400 }
      )
    }

    // 创建任务
    const newJob = await addCronJob({
      name: body.name,
      enabled: body.enabled ?? true,
      schedule: body.schedule,
      payload: body.payload,
      state: body.state || {
        next_run: Date.now()
      }
    })

    return NextResponse.json({
      data: newJob,
      success: true
    })
  } catch (error) {
    console.error('Failed to create cron job:', error)
    return NextResponse.json(
      {
        error: 'Failed to create cron job',
        details: (error as Error).message
      },
      { status: 500 }
    )
  }
}
