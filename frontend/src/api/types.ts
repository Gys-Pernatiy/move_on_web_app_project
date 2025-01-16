export interface StreakDay {
  date: string
  isCurrent: boolean
  coinsEarned: number
  bonusReceived: boolean
  bonusAvailable: boolean
}

export interface StreakHistoryResponse {
  days: StreakDay[]
  current_streak: number
  max_daily_streak: number
}

export interface walkUpdateData {
  walk_id: number,
  accX: number,
  accY: number,
  accZ: number,
  latitude: number,
  longitude: number,
  speed: number
}

export interface walkUpdateResponse {
  steps: number,
  distance: number,
  current_speed: number,
  average_speed: number
}

export interface walkStartResponse {
  walk_id: number,
  message: string,
  start_time: string
}

export interface walkStopResponse {
  reward: number
}
