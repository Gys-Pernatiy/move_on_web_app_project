import { useState } from 'react';
import CircularTimer from '../../components/CircularTimer';
import StrideCoins from '../../components/StrideCoins';
import StreakChart from '../../components/StreakChart';
import './MovePage.css';

const MovePage = () => {
    const [coins, setCoins] = useState(120);

    return (
        <div className="move-page">
            <StrideCoins coins={coins} measureUnit="Points" />
            <div className="timer-container">
                <CircularTimer
                    duration={1500}
                />
            </div>
            <StreakChart />
        </div>
    );
};

export default MovePage;
