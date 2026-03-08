import type { Metadata } from "next"
import "./globals.css"

export const metadata: Metadata = {
  title: "VersaClaw",
  description: "基于Nanobot扩展的AI Agent",
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
