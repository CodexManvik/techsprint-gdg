import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

export const ProtectedRoute = () => {
    const { isAuthenticated, isLoading } = useAuth();

    if (isLoading) {
        return <div className="flex items-center justify-center h-screen bg-black text-white">Loading...</div>; // Simple loader
    }

    if (!isAuthenticated) {
        return <Navigate to="/auth" replace />;
    }

    return <Outlet />;
};
