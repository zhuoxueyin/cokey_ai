import type { ChannelItem } from '@/types'
import {
  normalizeChatImageProtocolSlot,
  OPENAI_CHAT_IMAGE_LEGACY_SLOT,
} from '@/constants/protocol'

export interface ProfileOption {
  value: string
  label: string
  mode: string
  provider?: string
  protocol_slot?: string
  endpoint_type?: string
}

export function inferProviderFromProfileId(profileId: string): string | undefined {
  const prefix = profileId.split('.')[0]?.toLowerCase()
  if (prefix === 'openai') return '*'
  if (prefix === 'apiyi' || prefix === 'weelinking' || prefix === 'volcengine') return prefix
  return undefined
}

export function resolveProfileProvider(profile: Pick<ProfileOption, 'value' | 'provider'>): string | undefined {
  return profile.provider || inferProviderFromProfileId(profile.value)
}

export function resolveChannelProvider(
  channel?: Pick<ChannelItem, 'channel_code' | 'channel_provider'> | null,
): string | undefined {
  if (channel?.channel_provider) return channel.channel_provider
  const code = (channel?.channel_code || '').toLowerCase()
  if (code.includes('volcengine') || code.includes('volc')) return 'volcengine'
  if (code.includes('apiyi')) return 'apiyi'
  if (code.includes('weelink')) return 'weelinking'
  return undefined
}

/** 与后端 protocol_resolver 一致：* 表示全渠道通用 */
export function profileMatchesChannelProvider(
  profile: Pick<ProfileOption, 'value' | 'provider'>,
  channelProvider?: string | null,
): boolean {
  const pp = resolveProfileProvider(profile)
  if (!pp || pp === '*') return true
  if (!channelProvider) return false
  return pp === channelProvider
}

export function extractProfileModelFamily(profileId: string): string | undefined {
  const parts = profileId.split('.')
  if (parts.length < 2) return undefined
  const head = parts[1]
  if (head === 'gpt-image-2-all' || head === 'gpt-image-2-vip') return head
  if (head === 'gemini' || head === 'openai-image' || head === 'video') return head
  return head
}

export function inferChannelModelFamily(channelModelId?: string): string | undefined {
  const model = (channelModelId || '').toLowerCase()
  if (!model) return undefined
  if (model.includes('gpt-image-2-vip')) return 'gpt-image-2-vip'
  if (model.includes('gpt-image-2-all')) return 'gpt-image-2-all'
  if (model.includes('gemini') || model.includes('banana')) return 'gemini'
  if (model.includes('seedance') || model.includes('seedancer')) return 'video'
  return undefined
}

/** profile_id 模型族与 channel_model_id 对齐（如 banana 渠道不应选 gpt-image-2-vip 画像） */
export function profileMatchesChannelModel(
  profileId: string,
  channelModelId?: string,
): boolean {
  if (!channelModelId?.trim()) return true

  const profileFamily = extractProfileModelFamily(profileId)
  // Weelinking Images API 画像只绑定端点契约，model 字段原样透传，不与 model 名族硬绑定
  if (profileFamily === 'openai-image') return true

  const family = inferChannelModelFamily(channelModelId)
  if (!family) return true
  if (!profileFamily) return true
  return profileFamily === family
}

function profileOptionFromId(
  profiles: ProfileOption[],
  profileId: string,
  mode: string,
): ProfileOption {
  const known = profiles.find((p) => p.value === profileId)
  if (known) return known
  return {
    value: profileId,
    label: profileId,
    mode,
    provider: inferProviderFromProfileId(profileId),
  }
}

function isProfileCompatibleWithBinding(
  profile: ProfileOption,
  mode: string,
  channel?: Pick<ChannelItem, 'channel_code' | 'channel_provider' | 'endpoints'> | null,
  channelModelId?: string,
): boolean {
  return (
    profile.mode === mode &&
    profileMatchesChannelProvider(profile, resolveChannelProvider(channel)) &&
    channelSupportsProfile(channel, profile, mode) &&
    profileMatchesChannelModel(profile.value, channelModelId)
  )
}

export function explainProfileMismatch(
  profile: ProfileOption,
  mode: string,
  channel?: Pick<ChannelItem, 'channel_code' | 'channel_provider' | 'endpoints'> | null,
  channelModelId?: string,
): string | null {
  if (profile.mode !== mode) return `模式应为 ${mode}`
  if (!profileMatchesChannelProvider(profile, resolveChannelProvider(channel))) {
    return 'provider 与渠道不匹配'
  }
  if (!channelSupportsProfile(channel, profile, mode)) {
    return '渠道 endpoints 未覆盖该 protocol_slot'
  }
  if (!profileMatchesChannelModel(profile.value, channelModelId)) {
    const pf = extractProfileModelFamily(profile.value)
    const mf = inferChannelModelFamily(channelModelId || '')
    return `模型族不匹配（画像 ${pf} vs 模型 ${mf}）`
  }
  return null
}

function normalizeSlot(slot?: string, mode?: string): string | undefined {
  if (!slot) return undefined
  return normalizeChatImageProtocolSlot(slot) ?? slot
}

/** 协议画像的 slot/type 须被渠道 endpoints 覆盖 */
export function channelSupportsProfile(
  channel: Pick<ChannelItem, 'endpoints'> | null | undefined,
  profile: Pick<ProfileOption, 'protocol_slot' | 'endpoint_type'>,
  mode: string,
): boolean {
  const endpoints = channel?.endpoints || []
  if (!endpoints.length) return true

  const profileSlot = profile.protocol_slot
  const profileType = profile.endpoint_type

  for (const ep of endpoints) {
    const epSlot = ep.protocol_slot
    const epType = ep.type

    if (profileSlot && epSlot) {
      if (epSlot === OPENAI_CHAT_IMAGE_LEGACY_SLOT && profileSlot.startsWith('openai.chat.image')) {
        return true
      }
      if (normalizeSlot(profileSlot, mode) === normalizeSlot(epSlot, mode)) {
        return true
      }
    }

    if (profileType && epType && profileType === epType) {
      if (profileSlot && epSlot && profileSlot !== epSlot) continue
      return true
    }
  }
  return false
}

export function filterProfilesForBinding(
  profiles: ProfileOption[],
  mode: string,
  channel?: Pick<ChannelItem, 'channel_code' | 'channel_provider' | 'endpoints'> | null,
  channelModelId?: string,
  selectedProfileId?: string,
): ProfileOption[] {
  const filtered = profiles.filter((p) =>
    isProfileCompatibleWithBinding(p, mode, channel, channelModelId),
  )

  const selected = selectedProfileId?.trim()
  if (!selected || filtered.some((p) => p.value === selected)) {
    return filtered
  }

  const orphan = profileOptionFromId(profiles, selected, mode)
  const reason = explainProfileMismatch(orphan, mode, channel, channelModelId)
  return [
    {
      ...orphan,
      label: reason ? `${orphan.label}（当前配置 · ${reason}）` : `${orphan.label}（当前配置）`,
    },
    ...filtered,
  ]
}

export function pruneIncompatibleModeProfiles(
  modeProfiles: Record<string, string> | undefined,
  profiles: ProfileOption[],
  channel?: Pick<ChannelItem, 'channel_code' | 'channel_provider' | 'endpoints'> | null,
  channelModelId?: string,
): Record<string, string> {
  if (!modeProfiles) return {}
  const next: Record<string, string> = {}
  for (const [mode, profileId] of Object.entries(modeProfiles)) {
    if (!profileId?.trim()) continue
    const known = profiles.find((p) => p.value === profileId)
    const candidate = known || profileOptionFromId(profiles, profileId, mode)
    if (isProfileCompatibleWithBinding(candidate, mode, channel, channelModelId)) {
      next[mode] = profileId
    }
  }
  return next
}
