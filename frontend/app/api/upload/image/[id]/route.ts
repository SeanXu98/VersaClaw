import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.NANOBOT_API_URL || 'http://localhost:18790'

/**
 * GET /api/upload/image/[id]
 * 获取上传的图片（代理到后端）
 *
 * Query parameters:
 * - thumbnail: 如果存在，获取缩略图
 */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params
    const searchParams = request.nextUrl.searchParams
    const thumbnail = searchParams.get('thumbnail')

    // 构建后端 URL
    const backendUrl = thumbnail
      ? `${BACKEND_URL}/api/upload/image/${id}/thumbnail`
      : `${BACKEND_URL}/api/upload/image/${id}`

    const response = await fetch(backendUrl)

    if (!response.ok) {
      return NextResponse.json(
        { error: 'Image not found' },
        { status: 404 }
      )
    }

    const imageBuffer = await response.arrayBuffer()
    const contentType = response.headers.get('content-type') || 'image/png'

    return new NextResponse(imageBuffer, {
      headers: {
        'Content-Type': contentType,
        'Cache-Control': 'public, max-age=86400'
      }
    })
  } catch (error) {
    console.error('Image proxy error:', error)
    return NextResponse.json(
      { error: 'Failed to fetch image' },
      { status: 500 }
    )
  }
}
