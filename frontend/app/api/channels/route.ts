import { NextResponse } from 'next/server'
import { readConfig } from '@/lib/nanobot/config'
import type { ChannelName, ChannelMeta } from '@/types/nanobot'

/**
 * 渠道元数据
 */
const CHANNEL_METADATA: Record<ChannelName, Omit<ChannelMeta, 'name' | 'status' | 'message_count' | 'last_message_at' | 'error_message'>> = {
  telegram: {
    display_name: 'Telegram',
    icon: '📱'
  },
  discord: {
    display_name: 'Discord',
    icon: '🎮'
  },
  whatsapp: {
    display_name: 'WhatsApp',
    icon: '💬'
  },
  feishu: {
    display_name: '飞书 (Feishu)',
    icon: '🚀'
  },
  slack: {
    display_name: 'Slack',
    icon: '💼'
  },
  dingtalk: {
    display_name: '钉钉 (DingTalk)',
    icon: '📞'
  },
  mochat: {
    display_name: '企业微信 (Mochat)',
    icon: '🏢'
  },
  email: {
    display_name: 'Email',
    icon: '📧'
  },
  qq: {
    display_name: 'QQ',
    icon: '🐧'
  }
}

/**
 * GET /api/channels
 * 获取所有渠道列表及其配置状态
 */
export async function GET() {
  try {
    const config = await readConfig()
    const configuredChannels = config.channels || {}

    // 构建渠道列表
    const channels: ChannelMeta[] = Object.entries(CHANNEL_METADATA).map(([name, meta]) => {
      const channelConfig = configuredChannels[name]
      const isConfigured = !!channelConfig
      const isEnabled = isConfigured && channelConfig.enabled === true

      return {
        name: name as ChannelName,
        ...meta,
        status: isEnabled ? 'running' : (isConfigured ? 'stopped' : 'stopped'),
        message_count: 0 // TODO: 从sessions中统计
      }
    })

    // 统计
    const enabled = channels.filter(c => c.status === 'running').length
    const configured = channels.filter(c => configuredChannels[c.name]).length

    return NextResponse.json({
      data: {
        channels,
        total: channels.length,
        enabled,
        configured
      },
      success: true
    })
  } catch (error) {
    console.error('Failed to list channels:', error)
    return NextResponse.json(
      {
        error: 'Failed to retrieve channels',
        details: (error as Error).message
      },
      { status: 500 }
    )
  }
}
