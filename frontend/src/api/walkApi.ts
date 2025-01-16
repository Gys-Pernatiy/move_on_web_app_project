import fetchWithConfig from './apiConfig'
import { API_URL } from './const'
import { walkUpdateData, walkUpdateResponse, walkStartResponse, walkStopResponse } from './types'

export const startWalk = (data: {
    telegram_id: number
  }): Promise<walkStartResponse> => {
  return fetchWithConfig<any>(`${API_URL}/walks/`, {
    method: 'POST',
    data,
  })
}

export const updateWalk = (data: walkUpdateData): Promise<walkUpdateResponse> => {
  return fetchWithConfig<any>(`${API_URL}/walks/${data.walk_id}/`, {
    method: 'PUT',
    data,
  })
}

export const stopWalk = (data: {
    walk_id: number
  }): Promise<walkStopResponse> => {
  return fetchWithConfig<any>(`${API_URL}/walks/${data.walk_id}/finish/`, {
    method: 'POST',
    data,
  })
}