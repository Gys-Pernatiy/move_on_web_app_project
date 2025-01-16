import React from "react";
import useStepCounter from "./useStepCounter";

const StepCounter: React.FC = () => {
    const {stepCount} = useStepCounter();

    return (
        <div style={{ padding: "20px", textAlign: "center" }}>
            <h1>Шагомер</h1>
            <p>Количество шагов: {stepCount}</p>
        </div>
    );
};

export default StepCounter;
