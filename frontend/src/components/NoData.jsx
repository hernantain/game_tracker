import { Database } from 'lucide-react';
import { useLanguage } from '../i18n/LanguageContext';

/**
 * Placeholder for a chart whose data the SQL schema cannot answer yet.
 * `note` comes straight from GET /api/capabilities so the explanation lives
 * with the backend that knows why the data is missing.
 */
export default function NoData({ title, note, className = '' }) {
  const { t } = useLanguage();
  return (
    <div className={`card flex flex-col ${className}`}>
      {title && (
        <h3 className="text-sm font-semibold text-gray-300 mb-3">{title}</h3>
      )}
      <div className="flex-1 flex flex-col items-center justify-center text-center gap-2 py-8">
        <span className="p-2.5 rounded-xl bg-surface-2 text-gray-600">
          <Database size={20} />
        </span>
        <p className="text-sm font-medium text-gray-400">{t('noDataTitle')}</p>
        <p className="text-xs text-gray-600 max-w-xs">{note || t('noDataBody')}</p>
      </div>
    </div>
  );
}
