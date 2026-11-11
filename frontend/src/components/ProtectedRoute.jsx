import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import { useLanguage } from '../i18n/LanguageContext';

/**
 * Gate for routes that require a signed-in user. Use as a layout route:
 *   <Route element={<ProtectedRoute />}>
 *     <Route path="/favourites" element={<Favourites />} />
 *   </Route>
 * or wrap a single element: <ProtectedRoute><Favourites /></ProtectedRoute>
 */
export default function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  const { t } = useLanguage();
  const location = useLocation();

  if (loading) {
    return <div className="text-gray-500 text-sm">{t('loading')}</div>;
  }

  if (!user) {
    return <Navigate to="/login" replace state={{ from: location.pathname + location.search }} />;
  }

  return children ?? <Outlet />;
}
