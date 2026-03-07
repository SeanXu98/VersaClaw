import type { Metadata } from "next"
import "./globals.css"

export const metadata: Metadata = {
  title: "VersaClaw",
  description: "多模态 AI Agent 可视化管理平台",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  )
}
