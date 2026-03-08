import { NextResponse } from 'next/server'
import { readConfig } from '@/lib/nanobot/config'
import type { ProviderName, ProviderMeta } from '@/types/nanobot'

// Vision 模型检测模式（与 utils/model.ts 保持同步）
const VISION_MODEL_PATTERNS = [
  'gpt-4-vision', 'gpt-4-turbo', 'gpt-4o', 'gpt-4o-mini',
  'claude-3', 'claude-3.5',
  'gemini-1.5', 'gemini-2',
  'openrouter/', 'vision', 'llava',
  'glm-4v', 'qwen-vl', 'deepseek-vl'
]

function isVisionModel(model: string): boolean {
  const modelLower = model.toLowerCase()
  return VISION_MODEL_PATTERNS.some(pattern => modelLower.includes(pattern))
}

/**
 * 提供商元数据
 */
const PROVIDER_METADATA: Record<ProviderName, Omit<ProviderMeta, 'name' | 'status' | 'last_test' | 'test_result'>> = {
  // 网关
  openrouter: {
    display_name: 'OpenRouter',
    keywords: ['gateway', 'multi-model'],
    is_gateway: true,
    is_local: false,
    documentation_url: 'https://openrouter.ai/docs'
  },
  aihubmix: {
    display_name: 'AIHubMix',
    keywords: ['gateway', 'chinese'],
    is_gateway: true,
    is_local: false,
    documentation_url: 'https://aihubmix.com/docs'
  },
  custom: {
    display_name: 'Custom Gateway',
    keywords: ['gateway', 'custom'],
    is_gateway: true,
    is_local: false
  },
  // 国际
  anthropic: {
    display_name: 'Anthropic (Claude)',
    keywords: ['international', 'claude'],
    is_gateway: false,
    is_local: false,
    documentation_url: 'https://docs.anthropic.com'
  },
  openai: {
    display_name: 'OpenAI',
    keywords: ['international', 'gpt'],
    is_gateway: false,
    is_local: false,
    documentation_url: 'https://platform.openai.com/docs'
  },
  deepseek: {
    display_name: 'DeepSeek',
    keywords: ['international', 'reasoning'],
    is_gateway: false,
    is_local: false,
    documentation_url: 'https://platform.deepseek.com/docs'
  },
  groq: {
    display_name: 'Groq',
    keywords: ['international', 'fast'],
    is_gateway: false,
    is_local: false,
    documentation_url: 'https://console.groq.com/docs'
  },
  gemini: {
    display_name: 'Google Gemini',
    keywords: ['international', 'google'],
    is_gateway: false,
    is_local: false,
    documentation_url: 'https://ai.google.dev/docs'
  },
  // 国内
  dashscope: {
    display_name: '通义千问 (Qwen)',
    keywords: ['chinese', 'alibaba'],
    is_gateway: false,
    is_local: false,
    documentation_url: 'https://help.aliyun.com/zh/dashscope/'
  },
  moonshot: {
    display_name: 'Moonshot (Kimi)',
    keywords: ['chinese', 'kimi'],
    is_gateway: false,
    is_local: false,
    documentation_url: 'https://platform.moonshot.cn/docs'
  },
  zhipu: {
    display_name: '智谱 (GLM)',
    keywords: ['chinese', 'glm'],
    is_gateway: false,
    is_local: false,
    documentation_url: 'https://open.bigmodel.cn/dev/api'
  },
  minimax: {
    display_name: 'MiniMax',
    keywords: ['chinese'],
    is_gateway: false,
    is_local: false,
    documentation_url: 'https://www.minimaxi.com/document'
  },
  // 本地
  vllm: {
    display_name: 'vLLM (Local)',
    keywords: ['local', 'self-hosted'],
    is_gateway: false,
    is_local: true,
    documentation_url: 'https://docs.vllm.ai/'
  }
}

/**
 * GET /api/models/providers
 * 获取所有提供商列表及其配置状态
 */
export async function GET() {
  try {
    const config = await readConfig()
    const configuredProviders = config.providers || {}

    // 构建提供商列表
    const providers: ProviderMeta[] = Object.entries(PROVIDER_METADATA).map(([name, meta]) => {
      const isConfigured = name in configuredProviders
      const providerConfig = configuredProviders[name]
      const configuredModels = providerConfig?.models || []
      const visionModelsCount = configuredModels.filter(isVisionModel).length

      return {
        name: name as ProviderName,
        ...meta,
        status: isConfigured ? 'active' : 'inactive',
        configured_models: configuredModels,
        vision_models_count: visionModelsCount
      }
    })

    // 分类
    const categorized = {
      gateway: providers.filter(p => p.is_gateway),
      international: providers.filter(p => !p.is_gateway && !p.is_local && !p.keywords.includes('chinese')),
      chinese: providers.filter(p => !p.is_gateway && !p.is_local && p.keywords.includes('chinese')),
      local: providers.filter(p => p.is_local)
    }

    return NextResponse.json({
      data: {
        all: providers,
        categorized,
        configured: providers.filter(p => p.status === 'active').map(p => p.name)
      },
      success: true
    })
  } catch (error) {
    console.error('Failed to list providers:', error)
    return NextResponse.json(
      {
        error: 'Failed to retrieve providers',
        details: (error as Error).message
      },
      { status: 500 }
    )
  }
}
