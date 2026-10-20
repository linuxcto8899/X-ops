// ISO 3166-1 alpha-2 country code -> flag emoji
// Uses regional indicator symbols (U+1F1E6..U+1F1FF)
export function countryFlag(code) {
  if (!code) return ''
  const c = code.toUpperCase()
  if (!/^[A-Z]{2}$/.test(c)) return ''
  const base = 0x1f1e6
  return String.fromCodePoint(base + c.charCodeAt(0) - 65, base + c.charCodeAt(1) - 65)
}

// ISO country code -> real flag image URL (flagcdn). Works on all platforms
// (Windows does not render flag emoji, so we use images instead).
export function countryFlagImg(code) {
  if (!code) return ''
  const c = code.toLowerCase()
  if (!/^[a-z]{2}$/.test(c)) return ''
  return `https://flagcdn.com/w40/${c}.png`
}

// Common cloud regions -> ISO country code
const REGION_COUNTRY = {
  // China
  'cn': 'CN', 'cn-hangzhou': 'CN', 'cn-beijing': 'CN', 'cn-shanghai': 'CN',
  'cn-shenzhen': 'CN', 'cn-qingdao': 'CN', 'cn-zhangjiakou': 'CN', 'cn-huhehaote': 'CN',
  'cn-hongkong': 'HK', 'cn-hongkong-2': 'HK',
  // US
  'us-east-1': 'US', 'us-west-1': 'US', 'us-east-2': 'US', 'us-west-2': 'US',
  // Europe
  'eu-west-1': 'IE', 'eu-west-2': 'GB', 'eu-west-3': 'FR', 'eu-central-1': 'DE',
  'eu-north-1': 'SE', 'eu-south-1': 'IT',
  // Asia Pacific
  'ap-southeast-1': 'SG', 'ap-southeast-2': 'AU', 'ap-southeast-3': 'ID',
  'ap-northeast-1': 'JP', 'ap-northeast-2': 'KR', 'ap-northeast-3': 'JP',
  'ap-south-1': 'IN', 'ap-east-1': 'HK',
  // Others
  'sa-east-1': 'BR', 'ca-central-1': 'CA', 'me-south-1': 'BH', 'af-south-1': 'ZA',
  // Common short codes
  'us': 'US', 'jp': 'JP', 'kr': 'KR', 'sg': 'SG', 'hk': 'HK', 'de': 'DE',
  'fr': 'FR', 'uk': 'GB', 'gb': 'GB', 'au': 'AU', 'in': 'IN', 'br': 'BR',
  'ca': 'CA', 'ru': 'RU', 'tw': 'TW', 'mo': 'MO',
}

// Resolve region -> ISO country code
export function regionToCode(region, regionCode) {
  if (regionCode) return regionCode.toUpperCase()
  if (!region) return ''
  const key = region.toLowerCase()
  return REGION_COUNTRY[key] || key.toUpperCase()
}

export function regionToFlag(region, regionCode) {
  const code = regionToCode(region, regionCode)
  return countryFlag(code)
}

// Real flag image URL for a host (region + region_code)
export function regionFlagImg(region, regionCode) {
  return countryFlagImg(regionToCode(region, regionCode))
}

// Cloud provider display names
export const CLOUD_PROVIDERS = {
  '': '未选择',
  aliyun: '阿里云',
  tencent: '腾讯云',
  huawei: '华为云',
  aws: 'AWS',
  azure: 'Azure',
  gcp: 'GCP',
  oracle: 'Oracle Cloud',
  vultr: 'Vultr',
  linode: 'Linode',
  do: 'DigitalOcean',
  hetzner: 'Hetzner',
  self: '自建',
  other: '其他',
}