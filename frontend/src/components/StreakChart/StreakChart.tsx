import React, { useEffect, useState } from 'react'
import { getStreakHistory } from '../../api/api'
import { scaleContainer } from '../../utils/scaleContainer'
import { StreakHistoryResponse } from '../../api/types'
import { FaWalking, FaPlusCircle } from 'react-icons/fa'
import './StreakChart.css'

const StreakChart: React.FC = () => {
  const [streakData, setStreakData] = useState<StreakHistoryResponse | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    scaleContainer('.streak-chart-container', 0.9, 0.4);

    const fetchStreakData = async () => {
      try {
        const data = await getStreakHistory()
        setStreakData(data)
      } catch (error) {
        console.error('Error fetching streak data:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchStreakData()
  }, [])

  if (loading) {
    return <div className="streak-chart-loading">Loading...</div>
  }

  if (!streakData) {
    return null
  }

  const maxCoins = Math.max(...streakData.days.map(day => day.coinsEarned))

  return (
    <div className="streak-chart-container">
      <div className="streak-stats">
        <div className="streak-stat">
          <span className="streak-value">
            The <b>{streakData.current_streak}th</b> day in a row!
          </span>
        </div>
      </div>
      <div className="streak-chart">
        {streakData.days.map((day) => (
          <div key={day.date} className="streak-bar-wrapper">
            {day.bonusAvailable && (
              <FaPlusCircle
                className="gift-icon"
                style={{
                  color: day.bonusReceived ? '#f5f5f5' : '#ff0181',
                }}
              />
            )}
            <div
              className={`streak-bar ${day.coinsEarned > 0 ? 'earned' : 'not-earned'}`}
              style={{
                height: `${day.coinsEarned > 0 ? (day.coinsEarned / maxCoins) * 100 : 50}%`,
              }}
            >
              {day.isCurrent && <FaWalking className="walking-icon" />}
              {!day.isCurrent && day.coinsEarned > 0 && <div className="day-label">
                {new Date(day.date).toLocaleDateString('en-US', { weekday: 'short' })}
              </div>}
            </div>
            <div className="streak-coins" style={{ writingMode: 'vertical-rl', transform: 'rotate(180deg)' }}>
              {day.coinsEarned > 0 && day.coinsEarned}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default StreakChart;
