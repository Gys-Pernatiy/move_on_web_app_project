import React from 'react';
import { FaCoins } from 'react-icons/fa';
import './StatisticsPage.css';

interface GlobalStats {
    totalSteps: number;
    totalKilometers: number;
    todaySteps: number;
    todayKilometers: number;
}

interface PersonalStats {
    totalWalks: number;
    totalKilometers: number;
    totalSteps: number;
    totalTime: number;
}

interface Referral {
    id: string;
    name: string;
    coins: number;
}

const StatisticsPage = () => {
    // This would be fetched from backend
    const globalStats: GlobalStats = {
        totalSteps: 1234567,
        totalKilometers: 987,
        todaySteps: 45678,
        todayKilometers: 32
    };

    const personalStats: PersonalStats = {
        totalWalks: 42,
        totalKilometers: 156,
        totalSteps: 234567,
        totalTime: 3600 * 24 // in seconds
    };

    const referrals: Referral[] = [
        { id: '1', name: 'Alice', coins: 1200 },
        { id: '2', name: 'Bob', coins: 950 },
        { id: '3', name: 'Charlie', coins: 800 },
        { id: '4', name: 'David', coins: 600 },
        { id: '5', name: 'Eve', coins: 450 }
    ];

    const formatTime = (seconds: number): string => {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        return `${hours}h ${minutes}m`;
    };

    const formatNumber = (num: number): string => {
        return num.toLocaleString();
    };

    return (
        <div className="page">
            {/* Global Stats Block */}
            <div className="stats-block">
                <h2>Global Statistics</h2>
                <div className="global-stats">
                    <div className="stat-item">
                        <div className="stat-value">{formatNumber(globalStats.totalSteps)}</div>
                        <div className="stat-label">Total Steps</div>
                    </div>
                    <div className="stat-item">
                        <div className="stat-value">{globalStats.totalKilometers}km</div>
                        <div className="stat-label">Total Distance</div>
                    </div>
                    <div className="stat-item">
                        <div className="stat-value">{formatNumber(globalStats.todaySteps)}</div>
                        <div className="stat-label">Steps Today</div>
                    </div>
                    <div className="stat-item">
                        <div className="stat-value">{globalStats.todayKilometers}km</div>
                        <div className="stat-label">Distance Today</div>
                    </div>
                </div>
            </div>

            {/* Personal Stats Block */}
            <div className="stats-block">
                <h2>Your Statistics</h2>
                <div className="personal-stats">
                    <div className="stat-item">
                        <div className="stat-value">{personalStats.totalWalks}</div>
                        <div className="stat-label">Total Walks</div>
                    </div>
                    <div className="stat-item">
                        <div className="stat-value">{personalStats.totalKilometers}km</div>
                        <div className="stat-label">Total Distance</div>
                    </div>
                    <div className="stat-item">
                        <div className="stat-value">{formatNumber(personalStats.totalSteps)}</div>
                        <div className="stat-label">Total Steps</div>
                    </div>
                    <div className="stat-item">
                        <div className="stat-value">{formatTime(personalStats.totalTime)}</div>
                        <div className="stat-label">Total Time</div>
                    </div>
                </div>
            </div>

            {/* Referrals Block */}
            <div className="stats-block">
                <h2>Referrals</h2>
                <div className="referral-list-header">
                    <div className="referral-header-name">Total: <span>{referrals.length}</span></div>
                    <div className="referral-header-coins">Points</div>
                </div>
                <ul className="referral-list">
                    {referrals.map((referral, index) => (
                        <li key={referral.id} className="referral-item">
                            <div className="referral-name">
                                <span className="position-indicator">{index + 1}</span>
                                {referral.name}
                            </div>
                            <div className="referral-coins">
                                {formatNumber(referral.coins)}
                            </div>
                        </li>
                    ))}
                </ul>
            </div>
        </div>
    );
};

export default StatisticsPage;
