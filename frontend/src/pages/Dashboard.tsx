import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../lib/api';
import { useNavigate } from 'react-router-dom';

export const Dashboard = () => {
    const { user, logout } = useAuth();
    const [history, setHistory] = useState<any[]>([]);
    const navigate = useNavigate();

    useEffect(() => {
        const fetchHistory = async () => {
            try {
                const res = await api.get('/api/history');
                setHistory(res.data);
            } catch (err) {
                console.error(err);
            }
        };
        fetchHistory();
    }, []);

    return (
        <div className="min-h-screen bg-black text-white p-8">
            <div className="max-w-6xl mx-auto">
                <header className="flex justify-between items-center mb-12">
                    <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-pink-600">
                        Dashboard
                    </h1>
                    <div className="flex items-center gap-4">
                        <span className="text-neutral-400">Welcome, {user?.email}</span>
                        <button
                            onClick={logout}
                            className="px-4 py-2 rounded bg-neutral-800 hover:bg-neutral-700 transition-colors"
                        >
                            Logout
                        </button>
                    </div>
                </header>

                {/* Start New Session */}
                <section className="mb-12">
                    <div className="p-8 rounded-2xl bg-gradient-to-br from-purple-900/20 to-blue-900/20 border border-purple-500/20 flex flex-col items-center text-center">
                        <h2 className="text-2xl font-bold mb-4">Ready for your next interview?</h2>
                        <p className="text-neutral-400 mb-6 max-w-lg">
                            Practice with our advanced AI interviewer. Choose your persona and get real-time feedback.
                        </p>
                        <button
                            onClick={() => navigate('/lobby')}
                            className="px-8 py-3 rounded-full bg-white text-black font-bold hover:bg-neutral-200 transition-colors shadow-[0_0_20px_rgba(255,255,255,0.3)]"
                        >
                            Start New Session
                        </button>
                    </div>
                </section>

                {/* History Grid */}
                <section>
                    <h3 className="text-xl font-semibold mb-6 text-neutral-300">Recent Sessions</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {history.length === 0 ? (
                            <p className="text-neutral-500 col-span-full">No interview history yet.</p>
                        ) : (
                            history.map((session) => (
                                <div key={session.session_id} className="p-6 rounded-xl bg-neutral-900/50 border border-neutral-800 hover:border-purple-500/30 transition-colors cursor-pointer" onClick={() => navigate(`/report/${session.session_id}`)}>
                                    <div className="flex justify-between items-start mb-4">
                                        <span className="px-3 py-1 rounded-full text-xs bg-purple-500/10 text-purple-400 border border-purple-500/20">
                                            {session.persona}
                                        </span>
                                        <span className="text-xs text-neutral-500">
                                            {new Date(session.timestamp * 1000).toLocaleDateString()}
                                        </span>
                                    </div>
                                    <h4 className="text-lg font-medium mb-2">{session.topic}</h4>
                                    <p className="text-sm text-neutral-400 line-clamp-2">{session.summary || "No summary available."}</p>
                                </div>
                            ))
                        )}
                    </div>
                </section>
            </div>
        </div>
    );
};
