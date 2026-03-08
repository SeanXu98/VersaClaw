import { NextResponse } from 'next/server'
import { readConfig } from '@/lib/nanobot/config'

/**
 * GET /api/models/available
 * 获取所有已配置的可用模型列表
 */
export async function GET() {
  try {
    const config = await readConfig()
    const models: { provider: string; models: string[]; vision_models: string[] }[] = []

    // 定义每个提供商的默认模型（分类：文本模型 vs Vision 模型）
    const defaultModels: Record<string, { text: string[], vision: string[] }> = {
      zhipu: {
        // 文本模型：GLM-5 是最新旗舰，GLM-4.7/4.6 系列为推荐模型
        text: [
          'GLM-5',           // 最新旗舰模型
          'GLM-4.7',         // 推荐模型
          'GLM-4.7-FlashX',  // 快速版
          'GLM-4.7-Flash',   // 标准快速版
          'GLM-4.6',         // 稳定版
          'GLM-4.5-Air',     // 轻量版
          'GLM-4.5-AirX',    // 轻量增强版
          'GLM-4-Long',      // 长文本模型
        ],
        // Vision 模型：GLM-4.6V 系列为最新视觉模型
        vision: [
          'GLM-4.6V',              // 最新视觉模型
          'GLM-4.6V-Flash',        // 快速视觉模型
          'GLM-4.1V-Thinking-FlashX',  // 思维链视觉模型
          'GLM-4.1V-Thinking-Flash',   // 思维链视觉模型
          'GLM-4V-Flash',          // 轻量视觉模型
        ]
      },
      openai: {
        text: ['gpt-3.5-turbo', 'o1-preview', 'o1-mini'],
        vision: ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-4-vision-preview']
      },
      anthropic: {
        text: [],
        vision: ['claude-3-5-sonnet-20241022', 'claude-3-opus-20240229', 'claude-3-sonnet-20240229', 'claude-3-haiku-20240307']
      },
      deepseek: {
        text: ['deepseek-chat', 'deepseek-coder', 'deepseek-reasoner'],
        vision: []  // DeepSeek 暂无 Vision 模型
      },
      dashscope: {
        text: ['qwen-max', 'qwen-plus', 'qwen-turbo', 'qwen-long'],
        vision: ['qwen-vl-max', 'qwen-vl-plus', 'qwen-omni']  // 通义千问 VL 系列
      },
      moonshot: {
        text: ['moonshot-v1-8k', 'moonshot-v1-32k', 'moonshot-v1-128k'],
        vision: []  // Moonshot 暂无 Vision 模型
      },
      minimax: {
        text: ['abab6.5s-chat', 'abab6.5-chat', 'abab5.5-chat'],
        vision: ['abab6.5s-chat']  // MiniMax 部分模型支持 Vision
      },
      gemini: {
        text: ['gemini-1.5-flash-8b'],
        vision: ['gemini-2.0-flash-exp', 'gemini-1.5-pro', 'gemini-1.5-flash', 'gemini-pro']
      },
      groq: {
        text: ['llama-3.3-70b-versatile', 'llama-3.1-70b-versatile', 'llama-3.1-8b-instant', 'mixtral-8x7b-32768'],
        vision: ['llama-3.2-11b-vision-preview', 'llama-3.2-90b-vision-preview']  // Llama Vision
      },
      openrouter: {
        text: ['deepseek/deepseek-chat', 'meta-llama/llama-3.1-70b-instruct'],
        vision: ['anthropic/claude-3.5-sonnet', 'openai/gpt-4o', 'google/gemini-pro-1.5', 'meta-llama/llama-3.2-11b-vision-instruct']
      },
      aihubmix: {
        text: ['deepseek-chat'],
        vision: ['claude-3-5-sonnet-20241022', 'gpt-4o', 'gemini-1.5-pro']
      },
      custom: {
        text: [],
        vision: []
      },
      vllm: {
        text: [],
        vision: []
      },
    }

    // 遍历已配置的提供商
    if (config.providers) {
      for (const [providerName, providerConfig] of Object.entries(config.providers)) {
        // 检查是否有 API Key
        if (providerConfig && providerConfig.apiKey) {
          const defaults = defaultModels[providerName] || { text: [], vision: [] }

          // 如果提供商配置了特定模型，使用配置的模型
          if (providerConfig.models && providerConfig.models.length > 0) {
            // 用户自定义模型列表，需要自动检测 Vision 能力
            const visionPatterns = [
              'gpt-4-vision', 'gpt-4-turbo', 'gpt-4o', 'gpt-4o-mini',
              'claude-3', 'claude-3.5',
              'gemini-1.5', 'gemini-2',
              'qwen-vl', 'qwen-omni',
              'llama-3.2', 'llava', 'vision',
              'glm-4v', 'glm-4.6v', 'glm-4.1v'  // 智谱 GLM Vision 系列
            ]

            const textModels: string[] = []
            const visionModels: string[] = []

            for (const model of providerConfig.models) {
              const isVision = visionPatterns.some(p => model.toLowerCase().includes(p))
              if (isVision) {
                visionModels.push(model)
              } else {
                textModels.push(model)
              }
            }

            if (textModels.length > 0 || visionModels.length > 0) {
              models.push({
                provider: providerName,
                models: [...textModels, ...visionModels],
                vision_models: visionModels
              })
            }
          } else {
            // 使用默认模型列表
            const allModels = [...defaults.text, ...defaults.vision]
            if (allModels.length > 0) {
              models.push({
                provider: providerName,
                models: allModels,
                vision_models: defaults.vision
              })
            }
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
