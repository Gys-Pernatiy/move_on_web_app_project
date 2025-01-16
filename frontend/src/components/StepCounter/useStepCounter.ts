import { useEffect, useState, useRef } from "react";

// Constants for step detection
const ACCEL_THRESHOLD = 1.2; // Acceleration threshold for step detection
const GYRO_THRESHOLD = 0.8; // Gyroscope threshold for movement detection
const SPEED_THRESHOLD = 0.5; // Speed threshold in meters/second
const LOW_PASS_ALPHA = 0.8; // Low-pass filter coefficient

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

const useStepCounter = () => {
    const [stepCount, setStepCount] = useState(0); // Количество шагов
    const [sensorsAvailable, setSensorsAvailable] = useState(false); // Доступность сенсоров
    const [locationPermission, setLocationPermission] = useState<boolean | null>(null); // Права на геолокацию
    const [currentSpeed, setCurrentSpeed] = useState<number | null>(null); // Текущая скорость

    const webapp = window.Telegram.WebApp;

    // Предыдущее значение ускорения для фильтрации
    const lastAcceleration = useRef<AccelerometerEvent>({ x: 0, y: 0, z: 0 });
    const lastRotation = useRef<number>(0); // Предыдущее значение вращения

    // Обновление скорости из LocationManager
    const updateSpeedFromLocation = () => {
        console.log('locationPermission', locationPermission);
        // if (locationPermission) return;

        webapp.LocationManager.getLocation((data) => {
            console.log('data >>>>> ', data);
            const { speed } = data; // Скорость в метрах/секунду
            console.log('speed >>>>> ', speed);
            setCurrentSpeed(speed);
        });
    };

    // Подсчёт шага на основе акселерометра и гироскопа
    const detectStep = () => {
        const accel = webapp.Accelerometer;
        const gyro = webapp.Gyroscope;

        // Рассчитаем модуль ускорения
        const acceleration = Math.sqrt(accel.x * accel.x + accel.y * accel.y + accel.z * accel.z);

        // Рассчитаем модуль вращения
        const rotation = Math.sqrt(gyro.x * gyro.x + gyro.y * gyro.y + gyro.z * gyro.z);

        // Фильтруем шумы акселерометра (low-pass filter)
        const filteredAccel = LOW_PASS_ALPHA * acceleration + (1 - LOW_PASS_ALPHA) * lastAcceleration.current.z;
        lastAcceleration.current = { ...accel, z: filteredAccel };

        // Сохраняем текущую вращательную активность
        lastRotation.current = rotation;

        console.log('filteredAccel >>>> ', filteredAccel);
        console.log('rotation >>>> ', rotation);
        console.log('currentSpeed >>>> ', currentSpeed);
        console.log('stepCount >>>>>> ', stepCount);

        // Условие для подсчёта шага
        if (
            Math.abs(filteredAccel - 9.8) > ACCEL_THRESHOLD && // Ускорение превышает порог
            rotation > GYRO_THRESHOLD && // Вращение превышает порог
            currentSpeed !== null && currentSpeed > SPEED_THRESHOLD // Скорость больше порога
        ) {
            setStepCount((prev) => prev + 1);
        }
    };

    // Инициализация сенсоров
    useEffect(() => {
        if (!window.Telegram || !window.Telegram.WebApp) {
            console.warn("Telegram WebApp API недоступен.");
            return;
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
            webapp.onEvent('accelerometerChanged', detectStep);
        };

        // Ожидаем готовности WebApp и инициализируем сенсоры
        initSensors();

        // Очистка после размонтирования
        return () => {
            if (sensorsAvailable) {
                webapp.Accelerometer.stop();
                webapp.Gyroscope.stop();

                webapp.offEvent('accelerometerChanged', detectStep);
            }
        };
    }, []);

    return {
        stepCount,
        isMoving: stepCount > 0, // Если шаги фиксируются, пользователь движется
        sensorsAvailable,
        locationPermission,
        currentSpeed,
    };
};

export default useStepCounter;
