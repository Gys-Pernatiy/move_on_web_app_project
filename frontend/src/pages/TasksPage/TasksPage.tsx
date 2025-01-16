import React, { useState } from 'react';
import { FaPlus } from 'react-icons/fa';
import Logo from '../../components/Logo';
import './TasksPage.css';

interface Task {
    id: string;
    title: string;
    description: string;
    points: number;
    completed: boolean;
    icon: React.ReactNode;
    action: () => void;
}

const TasksPage = () => {
    const [tasks] = useState<Task[]>([
        {
            id: 'referral',
            title: 'Referral System',
            description: 'Invite a friend using your link and get 10% of their earnings',
            points: 100,
            completed: false,
            icon: <FaPlus size={24} color="#fff" />,
            action: () => {
                // Implement referral link sharing logic
                const referralLink = 'https://your-app.com/ref/USER_ID'; // Replace with actual referral link
                if (window.Telegram?.WebApp?.showPopup) {
                    window.Telegram.WebApp.showPopup({
                        title: 'Share Your Referral Link',
                        message: referralLink,
                        buttons: [
                            { type: 'default', text: 'Copy Link' }
                        ]
                    });
                }
            }
        },
        {
            id: 'emoji',
            title: 'Add Emoji to Status',
            description: 'Add our emoji to your Telegram status',
            points: 50,
            completed: false,
            icon: <Logo />,
            action: () => {
                // Implement status check logic
                if (window.Telegram?.WebApp?.showPopup) {
                    window.Telegram.WebApp.showPopup({
                        title: 'Add Emoji to Status',
                        message: 'Add 🚀 to your Telegram status to complete this task',
                        buttons: [
                            { type: 'default', text: 'OK' }
                        ]
                    });
                }
            }
        }
    ]);

    return (
        <div className="page">
            <div className="tasks-list">
                {tasks.map((task) => (
                    <div key={task.id} className="task-item">
                        <div className="task-info">
                            <div className="task-title">
                                <h3>{task.title}</h3>
                            </div>
                            <p>{task.description}</p>
                            <span className="points">+<b>{task.points}</b> points</span>
                        </div>
                        <button 
                            className={`task-button ${task.completed ? 'completed' : ''}`}
                            onClick={task.action}
                            disabled={task.completed}
                        >
                            {task.completed ? 'Completed' : 'Complete'}
                        </button>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default TasksPage;
