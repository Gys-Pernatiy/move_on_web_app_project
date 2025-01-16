import React, { useState, useLayoutEffect, useEffect, useRef } from 'react';
import { useTimer } from '../../context/TimerContext';
import Logo from '../Logo';
import './CircularTimer.css';
import useInitData from '../../hooks/useInitData';
import useStepCounter, { IAccumulateData } from '../../hooks/useStepCounter';
import { startWalk, updateWalk, stopWalk } from '../../api/walkApi';
import { scaleContainer } from '../../utils/scaleContainer'; 

interface CircularTimerProps {
    duration: number;
}

const CircularTimer: React.FC<CircularTimerProps> = ({
    duration
}) => {
    const { timeLeft, setTimeLeft, isRunning, setIsRunning } = useTimer();
    const [countdown, setCountdown] = useState(3);
    const [showCountdown, setShowCountdown] = useState(false);
    const [speed, setSpeed] = useState(0);
    const [canStop, setCanStop] = useState(false);
    
    const [walkId, setWalkId] = useState<number | null>(null);
    const [initDataUnsafe, initData] = useInitData();
    const { id } = initDataUnsafe?.user || {id: 1};
    
    const { accumulatedData, initSensors, resetAccumulatedData } = useStepCounter();
    const accumulatedDataRef = useRef(accumulatedData);
    useEffect(() => {
        accumulatedDataRef.current = accumulatedData;
      }, [accumulatedData]);

    const circleRef = useRef<SVGCircleElement>(null);
    const animationFrameRef = useRef<number>();
    const startTimeRef = useRef<number>();
    const lastStepTimeRef = useRef<number>();
    const sensorIntervalRef = useRef<number | null>(null);
    
    const CIRCLE_RADIUS = 165;
    const CIRCLE_CIRCUMFERENCE = 2 * Math.PI * CIRCLE_RADIUS;
    
    // Calculate marker position for 10 minutes (600 seconds)
    const tenMinutesAngle = -90 - (600 / duration * 360);
    const markerOuterX = 175 + (CIRCLE_RADIUS + 8) * Math.cos(tenMinutesAngle * Math.PI / 180);
    const markerInnerX = 175 + (CIRCLE_RADIUS - 8) * Math.cos(tenMinutesAngle * Math.PI / 180);
    const markerOuterY = 175 + (CIRCLE_RADIUS + 8) * Math.sin(tenMinutesAngle * Math.PI / 180);
    const markerInnerY = 175 + (CIRCLE_RADIUS - 8) * Math.sin(tenMinutesAngle * Math.PI / 180);
    
    useLayoutEffect(() => {
        setTimeLeft(duration);
    }, [duration]);

    useEffect(() => {
        if (timeLeft <= 0) {
            handleComplete();
        } else {
            requestAnimationFrame(updateSpeed);
        }
    }, [timeLeft]);

    useEffect(() => {
        if (isRunning && timeLeft <= 1490) {
            setCanStop(true);
        }
    }, [isRunning, timeLeft]);

    useEffect(() => {
        if (isRunning) {
            sensorIntervalRef.current = window.setInterval(() => {
                sendSensorData(accumulatedDataRef.current);
            }, 5000);

            return () => {
                if (sensorIntervalRef.current) {
                    clearInterval(sensorIntervalRef.current);
                    sensorIntervalRef.current = null;
                }
            };
        }
    }, [isRunning]);

    useEffect(() => {
        if (showCountdown && countdown > 0) {
            const timer = setTimeout(() => {
                setCountdown(prev => prev - 1);
            }, 1000);

            return () => clearTimeout(timer);
        } else if (showCountdown && countdown === 0) {
            setShowCountdown(false);
            startTimer();
        }
    }, [showCountdown, countdown]);

    const handleStart = async () => {
        if (!isRunning) {
            setShowCountdown(true);
            setCountdown(3);

            console.log('id', id);

            if (id) {
                try {
                    initSensors(); // Initialize sensors when starting the walk
                    const response = await startWalk({ telegram_id: id });
                    setWalkId(response.walk_id);
                } catch (error) {
                    console.error('Failed to start walk:', error);
                }
            }
        }
    };

    const startTimer = () => {
        setIsRunning(true);
        startTimeRef.current = Date.now();
    };

    const updateSpeed = () => {
        const randomSpeed = (Math.random() * (25.9 - 0.1) + 0.1).toFixed(1);
        setSpeed(parseFloat(randomSpeed));
        lastStepTimeRef.current = Date.now();
    };

    const sendSensorData = async (accumulatedData: IAccumulateData[]) => {
        // if (!walkId) return;

        console.log('accumulatedData', accumulatedData);

        // Get the last data point before resetting
        const lastDataPoint = accumulatedData[accumulatedData.length - 1];

        // Reset after getting the data we need
        resetAccumulatedData();

        try {
            const walkData = {
                walk_id: walkId || 1,
                accX: lastDataPoint?.accX || 0,
                accY: lastDataPoint?.accY || 0,
                accZ: lastDataPoint?.accZ || 0,
                latitude: lastDataPoint?.latitude || 0,
                longitude: lastDataPoint?.longitude || 0,
                speed: speed
            };

            const response = await updateWalk(walkData);
            // setSpeed(response.current_speed);
        } catch (error) {
            console.error('Failed to update walk:', error);
        }
    };

    const handleComplete = () => {
        setIsRunning(false);
        handleStop();
        if (animationFrameRef.current) {
            cancelAnimationFrame(animationFrameRef.current);
        }
    };

    const handleStop = async () => {
        if (canStop) {
            setIsRunning(false);
            setTimeLeft(duration);
            if (walkId) {
                try {
                    const response = await stopWalk({ walk_id: walkId });
                    setWalkId(null);
                } catch (error) {
                    console.error('Failed to stop walk:', error);
                }
            }
        }
    };

    // Cleanup on unmount
    useEffect(() => {
        scaleContainer('.circular-timer', 0.9, 0.45);
        return () => {
            if (sensorIntervalRef.current) {
                clearInterval(sensorIntervalRef.current);
                sensorIntervalRef.current = null;
            }
        };
    }, []);

    const progress = timeLeft / duration;
    const dashOffset = CIRCLE_CIRCUMFERENCE * (1 - progress);

    return (
        <div className="circular-timer">
            <svg width="350" height="350" viewBox="0 0 350 350">
                {/* Gradient definitions */}
                <defs>
                    <radialGradient id="progressGradient" cx="50%" cy="50%" r="50%" fx="50%" fy="50%">
                        <stop offset="0%" stopColor="#7ee8f4" />
                        <stop offset="90%" stopColor="#34bbdd" />
                        <stop offset="100%" stopColor="#00bcd4" />
                    </radialGradient>
                    <radialGradient id="backgroundGradient" cx="50%" cy="50%" r="50%" fx="50%" fy="50%">
                        <stop offset="0%" stopColor="rgba(0, 0, 0, 0.9)" />
                        <stop offset="70%" stopColor="rgba(255, 255, 255, 0.10)" />
                        <stop offset="100%" stopColor="rgba(255, 255, 255, 0.22)" />
                    </radialGradient>
                    <filter id="innerShadow" x="-20%" y="-20%" width="140%" height="140%">
                        <feGaussianBlur in="SourceAlpha" stdDeviation="3" result="blur" />
                        <feOffset in="blur" dx="2" dy="2" result="offsetBlur" />
                        <feComposite in="SourceAlpha" in2="offsetBlur" operator="out" result="innerShadow" />
                        <feFlood floodColor="rgba(0,0,0,0.3)" result="color" />
                        <feComposite in="color" in2="innerShadow" operator="in" result="shadow" />
                        <feComposite in="shadow" in2="SourceAlpha" operator="in" result="final" />
                        <feMerge>
                            <feMergeNode in="SourceGraphic" />
                            <feMergeNode in="final" />
                        </feMerge>
                    </filter>
                </defs>
                {/* Background circle */}
                <circle
                    cx="175"
                    cy="175"
                    r={CIRCLE_RADIUS}
                    className="timer-background"
                    stroke="url(#backgroundGradient)"
                    filter="url(#innerShadow)"
                />
                {/* Progress circle */}
                <circle
                    ref={circleRef}
                    cx="175"
                    cy="175"
                    r={CIRCLE_RADIUS}
                    className="timer-progress"
                    style={{
                        strokeDasharray: CIRCLE_CIRCUMFERENCE,
                        strokeDashoffset: dashOffset
                    }}
                    stroke="url(#progressGradient)"
                    transform="rotate(-90 175 175)"
                />
                {/* 10-minute marker */}
                {duration > 600 && (
                    <line
                        x1={markerInnerX}
                        y1={markerInnerY}
                        x2={markerOuterX}
                        y2={markerOuterY}
                        className="time-marker"
                    />
                )}
            </svg>
            
            <div className="timer-content">
                {showCountdown ? (
                    <div className="countdown">{countdown}</div>
                ) : !isRunning ? (
                    <button 
                        className="start-button" 
                        onClick={handleStart}
                        disabled={isRunning}
                    >
                        <Logo className="start-button-icon" />
                        <div className="start-button-text">START</div>
                    </button>
                ) : (
                    <>
                        <div className={`speed ${speed < 1 || speed > 20 ? 'invalid' : ''}`}>
                            <span className="speed-value">
                                {speed}
                            </span> km/h
                        </div>
                        {canStop && (
                            <button className="stop-button" onClick={handleStop}>
                                Stop
                            </button>
                        )}
                    </>
                )}
            </div>
        </div>
    );
};

export default CircularTimer;
