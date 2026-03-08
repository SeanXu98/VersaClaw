/**
 * 模型相关工具函数
 */

// Vision 模型检测模式
const VISION_MODEL_PATTERNS = [
  // OpenAI
  'gpt-4-vision',
  'gpt-4-turbo',
  'gpt-4o',
  'gpt-4o-mini',
  // Anthropic
  'claude-3',
  'claude-3.5',
  // Google
  'gemini-1.5',
  'gemini-2',
  // OpenRouter
  'openrouter/',
  // 智谱 GLM Vision 系列
  'glm-4v',
  'glm-4.6v',
  'glm-4.1v',
  // 其他可能的 Vision 模型
  'vision',
  'llava',
]

/**
 * 检测模型是否支持 Vision 能力
 */
export function isVisionModel(model: string | undefined | null): boolean {
  if (!model) return false
  const modelLower = model.toLowerCase()
  return VISION_MODEL_PATTERNS.some(pattern => modelLower.includes(pattern))
}
