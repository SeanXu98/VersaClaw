'use client'

import { useCallback, useState, useRef } from 'react'
import { Upload, X, Image as ImageIcon, Loader2 } from 'lucide-react'
import type { UploadedImage } from '@/types/nanobot'

// 后端 API 地址
const BACKEND_URL = process.env.NEXT_PUBLIC_NANOBOT_API_URL || 'http://localhost:18790'

// 获取完整的图片 URL
function getFullImageUrl(url: string): string {
  if (url.startsWith('http://') || url.startsWith('https://') || url.startsWith('data:')) {
    return url
  }
  // 相对路径，添加后端地址
  return `${BACKEND_URL}${url}`
}

interface ImageUploaderProps {
  onUploadSuccess: (images: UploadedImage[]) => void
  onUploadError?: (error: string) => void
  maxFiles?: number
  maxSize?: number  // MB
  disabled?: boolean
  pendingImages?: UploadedImage[]
  onRemoveImage?: (imageId: string) => void
}

const ACCEPTED_TYPES = ['image/png', 'image/jpeg', 'image/gif', 'image/webp']
const DEFAULT_MAX_SIZE = 10 // MB

export default function ImageUploader({
  onUploadSuccess,
  onUploadError,
  maxFiles = 5,
  maxSize = DEFAULT_MAX_SIZE,
  disabled = false,
  pendingImages = [],
  onRemoveImage,
}: ImageUploaderProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [uploadingFiles, setUploadingFiles] = useState<string[]>([])
  const fileInputRef = useRef<HTMLInputElement>(null)

  // 是否还可以上传更多
  const canUploadMore = pendingImages.length < maxFiles && !disabled

  // 验证文件
  const validateFile = useCallback((file: File): string | null => {
    if (!ACCEPTED_TYPES.includes(file.type)) {
      return `不支持的文件类型: ${file.type}。支持: PNG, JPG, GIF, WebP`
    }
    if (file.size > maxSize * 1024 * 1024) {
      return `文件太大: ${(file.size / 1024 / 1024).toFixed(2)}MB，最大: ${maxSize}MB`
    }
    return null
  }, [maxSize])

  // 上传单个文件
  const uploadFile = useCallback(async (file: File): Promise<UploadedImage | null> => {
    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch('/api/upload/image', {
        method: 'POST',
        body: formData,
      })

      const data = await response.json()

      if (data.success && data.data) {
        return data.data as UploadedImage
      } else {
        onUploadError?.(data.error || '上传失败')
        return null
      }
    } catch (error) {
      console.error('Upload error:', error)
      onUploadError?.(error instanceof Error ? error.message : '上传失败')
      return null
    }
  }, [onUploadError])

  // 处理文件
  const handleFiles = useCallback(async (files: FileList | File[]) => {
    if (disabled) return

    const fileArray = Array.from(files)
    const availableSlots = maxFiles - pendingImages.length

    if (availableSlots <= 0) {
      onUploadError?.(`最多上传 ${maxFiles} 张图片`)
      return
    }

    const filesToUpload = fileArray.slice(0, availableSlots)

    // 验证所有文件
    for (const file of filesToUpload) {
      const error = validateFile(file)
      if (error) {
        onUploadError?.(error)
        return
      }
    }

    // 标记正在上传
    setUploadingFiles(prev => [...prev, ...filesToUpload.map(f => f.name)])

    try {
      const uploadPromises = filesToUpload.map(uploadFile)
      const results = await Promise.all(uploadPromises)

      const successfulUploads = results.filter((img): img is UploadedImage => img !== null)

      if (successfulUploads.length > 0) {
        onUploadSuccess(successfulUploads)
      }
    } finally {
      setUploadingFiles(prev => prev.filter(name => !filesToUpload.some(f => f.name === name)))
    }
  }, [disabled, pendingImages.length, maxFiles, validateFile, uploadFile, onUploadSuccess, onUploadError])

  // 点击上传
  const handleClick = useCallback(() => {
    if (!disabled && pendingImages.length < maxFiles) {
      fileInputRef.current?.click()
    }
  }, [disabled, pendingImages.length, maxFiles])

  // 文件选择变化
  const handleFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      handleFiles(files)
    }
    e.target.value = ''
  }, [handleFiles])

  // 拖拽事件
  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (!disabled) {
      setIsDragging(true)
    }
  }, [disabled])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
  }, [])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)

    if (!disabled) {
      const files = e.dataTransfer.files
      if (files.length > 0) {
        handleFiles(files)
      }
    }
  }, [disabled, handleFiles])

  // 删除图片
  const handleRemove = useCallback((imageId: string) => {
    onRemoveImage?.(imageId)
  }, [onRemoveImage])

  return (
    <div className="image-uploader">
      {/* 上传区域 */}
      <div
        onClick={handleClick}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        className={`
          relative border-2 border-dashed rounded-lg p-3 text-center cursor-pointer transition-all
          ${disabled
            ? 'border-slate-200 bg-slate-50 text-slate-400 cursor-not-allowed'
            : isDragging
              ? 'border-blue-500 bg-blue-50 text-blue-600'
              : canUploadMore
                ? 'border-slate-300 hover:border-blue-400 hover:bg-slate-50 text-slate-500 hover:text-blue-500'
                : 'border-slate-200 bg-slate-50 text-slate-400 cursor-not-allowed'
          }
        `}
      >
        {/* 隐藏的文件输入 */}
        <input
          ref={fileInputRef}
          type="file"
          accept="image/png,image/jpeg,image/gif,image/webp"
          multiple
          onChange={handleFileChange}
          className="hidden"
          disabled={disabled || !canUploadMore}
        />

        {/* 上传图标和文字 */}
        <div className="flex items-center justify-center gap-2">
          {uploadingFiles.length > 0 ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span className="text-sm">上传中...</span>
            </>
          ) : (
            <>
              {canUploadMore ? (
                <>
                  <Upload className="w-4 h-4" />
                  <span className="text-sm">
                    点击或拖拽上传图片
                    <span className="text-xs text-slate-400 ml-1">
                      ({pendingImages.length}/{maxFiles})
                    </span>
                  </span>
                </>
              ) : (
                <>
                  <ImageIcon className="w-4 h-4" />
                  <span className="text-sm">已达最大数量 ({maxFiles}张)</span>
                </>
              )}
            </>
          )}
        </div>

        {/* 提示信息 */}
        {canUploadMore && (
          <p className="text-xs text-slate-400 mt-1">
            支持 PNG, JPG, GIF, WebP，最大 {maxSize}MB
          </p>
        )}
      </div>

      {/* 已上传的图片预览 */}
      {pendingImages.length > 0 && (
        <div className="flex flex-wrap gap-2 mt-3">
          {pendingImages.map((image) => (
            <div
              key={image.id}
              className="relative group"
            >
              <img
                src={getFullImageUrl(image.thumbnail_url || image.url)}
                alt={image.filename}
                className="w-16 h-16 object-cover rounded-lg border border-slate-200"
              />
              <button
                type="button"
                onClick={() => handleRemove(image.id)}
                className="absolute -top-2 -right-2 w-5 h-5 bg-red-500 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center"
                disabled={disabled}
              >
                <X className="w-3 h-3" />
              </button>
              <div className="absolute bottom-0 left-0 right-0 bg-black/50 text-white text-xs p-1 rounded-b-lg truncate opacity-0 group-hover:opacity-100 transition-opacity">
                {image.filename}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
