import { NextRequest, NextResponse } from 'next/server'
import { getCronJob, updateCronJob, deleteCronJob } from '@/lib/nanobot/cron'

/**
 * GET /api/cron/[id]
 * 获取单个定时任务
 */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params
    const job = await getCronJob(id)

    if (!job) {
      return NextResponse.json(
        { error: 'Cron job not found' },
        { status: 404 }
      )
    }

    return NextResponse.json({
      data: job,
      success: true
    })
  } catch (error) {
    console.error('Failed to get cron job:', error)
    return NextResponse.json(
      {
        error: 'Failed to retrieve cron job',
        details: (error as Error).message
      },
      { status: 500 }
    )
  }
}

/**
 * PATCH /api/cron/[id]
 * 更新定时任务
 */
export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params
    const updates = await request.json()

    await updateCronJob(id, updates)

    return NextResponse.json({
      data: { message: 'Cron job updated successfully' },
      success: true
    })
  } catch (error) {
    const errorMessage = (error as Error).message

    if (errorMessage.includes('not found')) {
      return NextResponse.json(
        { error: 'Cron job not found' },
        { status: 404 }
      )
    }

    console.error('Failed to update cron job:', error)
    return NextResponse.json(
      {
        error: 'Failed to update cron job',
        details: errorMessage
      },
      { status: 500 }
    )
  }
}

/**
 * DELETE /api/cron/[id]
 * 删除定时任务
 */
export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params
    await deleteCronJob(id)

    return NextResponse.json({
      data: { message: 'Cron job deleted successfully' },
      success: true
    })
  } catch (error) {
    const errorMessage = (error as Error).message

    if (errorMessage.includes('not found')) {
      return NextResponse.json(
        { error: 'Cron job not found' },
        { status: 404 }
      )
    }

    console.error('Failed to delete cron job:', error)
    return NextResponse.json(
      {
        error: 'Failed to delete cron job',
        details: errorMessage
      },
      { status: 500 }
    )
  }
}
