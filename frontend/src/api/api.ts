import fetchWithConfig from './apiConfig'
import { StreakHistoryResponse } from './types'
import { API_URL } from './const'

export const getStreakHistory = (): Promise<StreakHistoryResponse> => {
  // Mock data
  const mockData: StreakHistoryResponse = {
    days: [
      {
        date: '2024-11-26',
        isCurrent: false,
        coinsEarned: 315,
        bonusReceived: true,
        bonusAvailable: false
      },
      {
        date: '2024-11-27',
        isCurrent: false,
        coinsEarned: 200,
        bonusReceived: true,
        bonusAvailable: false
      },
      {
        date: '2024-11-28',
        isCurrent: false,
        coinsEarned: 425,
        bonusReceived: true,
        bonusAvailable: false
      },
      {
        date: '2024-11-29',
        isCurrent: false,
        coinsEarned: 280,
        bonusReceived: true,
        bonusAvailable: false
      },
      {
        date: '2024-11-30',
        isCurrent: false,
        coinsEarned: 350,
        bonusReceived: true,
        bonusAvailable: true
      },
      {
        date: '2024-12-01',
        isCurrent: false,
        coinsEarned: 100,
        bonusReceived: true,
        bonusAvailable: false
      },
      {
        date: '2024-12-02',
        isCurrent: false,
        coinsEarned: 115,
        bonusReceived: true,
        bonusAvailable: false
      },
      {
        date: '2024-12-03',
        isCurrent: true,
        coinsEarned: 0,
        bonusReceived: false,
        bonusAvailable: false
      },
      {
        date: '2024-12-04',
        isCurrent: false,
        coinsEarned: 0,
        bonusReceived: false,
        bonusAvailable: false
      },
      {
        date: '2024-12-05',
        isCurrent: false,
        coinsEarned: 0,
        bonusReceived: false,
        bonusAvailable: false
      },
      {
        date: '2024-12-06',
        isCurrent: false,
        coinsEarned: 0,
        bonusReceived: true,
        bonusAvailable: true
      },
      {
        date: '2024-12-07',
        isCurrent: false,
        coinsEarned: 0,
        bonusReceived: false,
        bonusAvailable: false
      },
      {
        date: '2024-12-08',
        isCurrent: false,
        coinsEarned: 0,
        bonusReceived: false,
        bonusAvailable: false
      },
      {
        date: '2024-12-09',
        isCurrent: false,
        coinsEarned: 0,
        bonusReceived: false,
        bonusAvailable: false
      },
      {
        date: '2024-12-10',
        isCurrent: false,
        coinsEarned: 0,
        bonusReceived: false,
        bonusAvailable: true
      }
    ],
    current_streak: 8,
    max_daily_streak: 15
  }

  // Return mock data as a promise
  return Promise.resolve(mockData)
}
