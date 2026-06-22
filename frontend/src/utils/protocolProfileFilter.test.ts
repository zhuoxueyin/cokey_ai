import { describe, expect, it } from 'vitest'
import type { ChannelItem } from '@/types'
import { BUILTIN_PROFILE_OPTIONS } from '@/constants/onboarding'
import {
  filterProfilesForBinding,
  profileMatchesChannelModel,
  pruneIncompatibleModeProfiles,
} from '@/utils/protocolProfileFilter'

const WEELINK_IMAGE_CHANNEL: Pick<ChannelItem, 'channel_code' | 'channel_provider' | 'endpoints'> = {
  channel_code: 'weelink_image',
  channel_provider: 'weelinking',
  endpoints: [
    { type: 'image', protocol_slot: 'openai.images.generations', endpoint: 'images/generations' },
    { type: 'image_edits', protocol_slot: 'openai.images.edits', endpoint: 'images/edits' },
  ],
}

describe('profileMatchesChannelModel', () => {
  it('allows weelinking.openai-image for gemini model id (Images API passthrough)', () => {
    expect(
      profileMatchesChannelModel(
        'weelinking.openai-image.text_to_image',
        'gemini-3-pro-image-preview',
      ),
    ).toBe(true)
  })

  it('blocks gpt-image-2-vip profile for gemini model', () => {
    expect(
      profileMatchesChannelModel(
        'apiyi.gpt-image-2-vip.text_to_image',
        'gemini-3-pro-image-preview',
      ),
    ).toBe(false)
  })
})

describe('filterProfilesForBinding', () => {
  it('lists weelink openai-image profiles for gemini on weelink gpt-image channel', () => {
    const options = filterProfilesForBinding(
      BUILTIN_PROFILE_OPTIONS,
      'text_to_image',
      WEELINK_IMAGE_CHANNEL,
      'gemini-3-pro-image-preview',
    )
    expect(options.some((o) => o.value === 'weelinking.openai-image.text_to_image')).toBe(true)
  })

  it('keeps saved profile visible even when incompatible', () => {
    const options = filterProfilesForBinding(
      BUILTIN_PROFILE_OPTIONS,
      'text_to_image',
      WEELINK_IMAGE_CHANNEL,
      'gemini-3-pro-image-preview',
      'apiyi.gpt-image-2-vip.text_to_image',
    )
    expect(options[0]?.value).toBe('apiyi.gpt-image-2-vip.text_to_image')
    expect(options[0]?.label).toContain('当前配置')
  })
})

describe('pruneIncompatibleModeProfiles', () => {
  it('preserves weelinking.openai-image for gemini model id', () => {
    const next = pruneIncompatibleModeProfiles(
      { text_to_image: 'weelinking.openai-image.text_to_image' },
      BUILTIN_PROFILE_OPTIONS,
      WEELINK_IMAGE_CHANNEL,
      'gemini-3-pro-image-preview',
    )
    expect(next.text_to_image).toBe('weelinking.openai-image.text_to_image')
  })
})
