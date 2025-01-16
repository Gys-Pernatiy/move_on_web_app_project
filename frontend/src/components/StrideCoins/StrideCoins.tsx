import React from 'react';
import { FaCoins } from 'react-icons/fa';
import './StrideCoins.css';

interface StrideCoinProps {
    coins: number;
    measureUnit: string;
}

const StrideCoins: React.FC<StrideCoinProps> = ({ coins, measureUnit }) => {
    return (
        <div className="stride-coins">
            {measureUnit}:
            <span className="coins-amount">{coins}</span>
        </div>
    );
};

export default StrideCoins;
