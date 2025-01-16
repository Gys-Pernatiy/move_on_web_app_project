import fetchWithConfig from './apiConfig'
import { API_URL } from './const'

export const saveLeaderboard = (data: any): Promise<any> => {
  return fetchWithConfig<any>(`${API_URL}/leaderboard/`, {
    method: 'POST',
    data,
  })
}

export const getLeaderboard = (data: any): Promise<any> => {
  return fetchWithConfig<any>(`${API_URL}/leaderboard/all/`, {
    method: 'POST',
    data,
  })
}
