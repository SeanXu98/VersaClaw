import { NextResponse } from 'next/server'
import { readConfig } from '@/lib/nanobot/config'

/**
 * GET /api/models/available
 * 获取所有已配置的可用模型列表
 */
export async function GET() {
  try {
    const config = await readConfig()
    const models: { provider: string; models: string[] }[] = []

    // 定义每个提供商的默认模型
    const defaultModels: Record<string, string[]> = {
      zhipu: ['glm-4', 'glm-4-flash', 'glm-4-plus', 'glm-3-turbo'],
      openai: ['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo'],
      anthropic: ['claude-3-opus', 'claude-3-sonnet', 'claude-3-haiku'],
      deepseek: ['deepseek-chat', 'deepseek-coder'],
      dashscope: ['qwen-max', 'qwen-plus', 'qwen-turbo'],
      moonshot: ['moonshot-v1-8k', 'moonshot-v1-32k', 'moonshot-v1-128k'],
      minimax: ['abab6.5-chat', 'abab5.5-chat'],
      gemini: ['gemini-pro', 'gemini-pro-vision'],
      groq: ['llama3-70b-8192', 'llama3-8b-8192', 'mixtral-8x7b-32768'],
      openrouter: ['anthropic/claude-3-opus', 'openai/gpt-4', 'meta-llama/llama-3-70b'],
      aihubmix: ['claude-3-opus', 'gpt-4', 'gemini-pro'],
      custom: [],
      vllm: [],
    }

    // 遍历已配置的提供商
    if (config.providers) {
      for (const [providerName, providerConfig] of Object.entries(config.providers)) {
        // 检查是否有 API Key
        if (providerConfig && providerConfig.apiKey) {
          // 如果提供商配置了特定模型，使用配置的模型
          // 否则使用默认模型列表
          const providerModels = providerConfig.models && providerConfig.models.length > 0
            ? providerConfig.models
            : (defaultModels[providerName] || [])

          if (providerModels.length > 0) {
            models.push({
              provider: providerName,
              models: providerModels
            })
          }
        }
      }
    }

    return NextResponse.json({
      success: true,
      data: { models }
    })
  } catch (error) {
    console.error('Failed to get available models:', error)
    return NextResponse.json(
      {
        error: 'Failed to get available models',
        details: (error as Error).message
      },
      { status: 500 }
    )
  }
}
