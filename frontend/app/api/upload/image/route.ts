import { NextResponse } from 'next/server'
import type { UploadedImage, UploadImageResponse } from '@/types/nanobot'

const BACKEND_URL = process.env.NANOBOT_API_URL || 'http://localhost:18790'

export async function POST(request: Request) {
  try {
    const formData = await request.formData()
    const file = formData.get('file') as File | null

    if (!file) {
      return NextResponse.json(
        { success: false, error: '没有选择文件' } as UploadImageResponse,
        { status: 400 }
      )
    }

    const backendFormData = new FormData()
    backendFormData.append('file', file)

    const response = await fetch(`${BACKEND_URL}/api/upload/image`, {
      method: 'POST',
      body: backendFormData,
    })

    const data: UploadImageResponse = await response.json()

    return NextResponse.json(data, { status: response.status })
  } catch (error) {
    console.error('Upload proxy error:', error)
    return NextResponse.json(
      { success: false, error: '上传失败，请稍后重试' } as UploadImageResponse,
      { status: 500 }
    )
  }
}
