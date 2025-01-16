import React, { createContext, useState, useContext, ReactNode, useEffect, useRef } from 'react';

interface TimerContextProps {
    timeLeft: number;
    setTimeLeft: (time: number) => void;
    isRunning: boolean;
    setIsRunning: (running: boolean) => void;
}

const TimerContext = createContext<TimerContextProps | undefined>(undefined);

export const TimerProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
    const [timeLeft, setTimeLeft] = useState(0);
    const [isRunning, setIsRunning] = useState(false);
    const timerRef = useRef<number | null>(null);

    useEffect(() => {
        if (isRunning && timeLeft > 0) {
            timerRef.current = setInterval(() => {
                setTimeLeft(prev => prev - 1);
            }, 1000);
        } else if (!isRunning || timeLeft <= 0) {
            if (timerRef.current) {
                clearInterval(timerRef.current);
            }
        }

        return () => {
            if (timerRef.current) {
                clearInterval(timerRef.current);
            }
        };
    }, [isRunning, timeLeft]);

    return (
        <TimerContext.Provider value={{ timeLeft, setTimeLeft, isRunning, setIsRunning }}>
            {children}
        </TimerContext.Provider>
    );
};

export const useTimer = () => {
    const context = useContext(TimerContext);
    if (!context) {
        throw new Error('useTimer must be used within a TimerProvider');
    }
    return context;
};
