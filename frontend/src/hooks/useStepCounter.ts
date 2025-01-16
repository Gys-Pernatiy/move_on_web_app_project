import { useEffect, useState, useRef } from "react";
import useWebApp from "./useWebApp";

interface AccelerometerEvent {
    x: number;
    y: number;
    z: number;
}

interface GyroscopeData {
    x: number;
    y: number;
    z: number;
}

export interface IAccumulateData {
    accX: number,
    accY: number,
    accZ: number,
    gyroX: number,
    gyroY: number,
    gyroZ: number,
    latitude: number,
    longitude: number,
    speed: number | null
}

const useStepCounter = () => {
    const [sensorsAvailable, setSensorsAvailable] = useState(false); // Доступность сенсоров
    const [locationPermission, setLocationPermission] = useState<boolean | null>(null); // Права на геолокацию
    const [currentSpeed, setCurrentSpeed] = useState<number | null>(null); // Текущая скорость
    const [accumulatedData, setAccumulatedData] = useState<IAccumulateData[]>([]);

    const webapp = useWebApp() || window.Telegram.WebApp;

    // Обновление скорости из LocationManager
    const updateSpeedFromLocation = () => {
        console.log('locationPermission ~~~~~~', locationPermission);
        // if (locationPermission) return;

        webapp.LocationManager.getLocation((data) => {
            const { speed } = data; // Скорость в метрах/секунду
            setCurrentSpeed(speed);
        });
    };

    const resetAccumulatedData = () => {
        setAccumulatedData([]);
    };

    const accumulateData = () => {
        const { x: accX, y: accY, z: accZ } = webapp.Accelerometer;
        const { x: gyroX, y: gyroY, z: gyroZ } = webapp.Gyroscope; 

        webapp.LocationManager.getLocation((data) => {
            const { speed, latitude, longitude } = data;

            setAccumulatedData(prev => [...prev, { accX, accY, accZ, gyroX, gyroY, gyroZ, latitude, longitude, speed }]);
        });
    }

    // Проверка наличия сенсоров
    const checkSensors = () => {
        const hasAccel = Boolean(webapp.Accelerometer);
        const hasGyro = Boolean(webapp.Gyroscope);
        const hasLocation = Boolean(webapp.LocationManager);

        setSensorsAvailable(hasAccel && hasGyro && hasLocation);
        return hasAccel && hasGyro && hasLocation;
    };

    // Инициализация сенсоров
    const initSensors = () => {
        if (!window.Telegram || !window.Telegram.WebApp) {
            console.warn("Telegram WebApp API недоступен.");
            return;
        }

        if (!checkSensors()) {
            console.warn("Some sensors are not available");
            return;
        }

        // Запуск сенсоров
        webapp.Accelerometer.start();
        webapp.Gyroscope.start();

        // Инициализация геолокации
        webapp.LocationManager.init(() => {
            const { isInited, isLocationAvailable, isAccessGranted } = webapp.LocationManager;

            const permission = isInited && isLocationAvailable && isAccessGranted;

            console.log('permission', permission);

            if (!permission) webapp.LocationManager.openSettings();

            setLocationPermission(permission);

            // Получение начальной скорости
            updateSpeedFromLocation();

            // Обновление скорости с периодичностью
            const locationInterval = setInterval(updateSpeedFromLocation, 1000); // Обновляем каждую секунду

            // Очистка интервала при размонтировании
            return () => clearInterval(locationInterval);
        });

        // Слушатели событий
        webapp.onEvent('gyroscopeChanged', accumulateData);
        webapp.onEvent('accelerometerChanged', accumulateData);
    };

    // Очистка после размонтирования
    useEffect(() => {
        return () => {
            if (sensorsAvailable) {
                webapp.Accelerometer.stop();
                webapp.Gyroscope.stop();

                webapp.offEvent('gyroscopeChanged', accumulateData);
                webapp.offEvent('accelerometerChanged', accumulateData);
            }
        };
    }, []);

    return {
        accumulatedData,
        sensorsAvailable,
        locationPermission,
        currentSpeed,
        initSensors,
        resetAccumulatedData
    };
};

export default useStepCounter;
