import { useEffect, useState } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LabelList,
} from 'recharts';
import { useIsMobile } from '../hooks/useIsMobile';
import { useLanguage } from '../i18n/LanguageContext';
import { api } from '../api';
import NoData from '../components/NoData';
import { useCapabilities } from '../hooks/useCapabilities';

const TABS = [
  { key: 'topScorers',      labelKey: 'tabTopScorers'      },
  { key: 'mostAppearances', labelKey: 'tabMostAppearances' },
  { key: 'mostBench',       labelKey: 'tabMostBench'       },
  { key: 'mostTotal',       labelKey: 'tabMostTotal'       },
];

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-surface-1 border border-surface-3 rounded-lg p-3 text-sm shadow-xl">
      <p className="text-gray-400 mb-1">{label}</p>
      {payload.map(p => <p key={p.name} style={{ color: p.color }}>{p.name}: <b>{p.value}</b></p>)}
    </div>
  );
};

function PlayerTable({ players, valueKey, maxValue, color = '#00A8E8' }) {
  return (
    <div className="space-y-2">
      {players.map((p, i) => (
        <div key={p.name} className="flex items-center gap-3 text-sm group hover:bg-surface-2 px-2 py-1.5 rounded-lg transition-colors">
          <span className="text-gray-600 w-6 text-right text-xs font-mono">{i + 1}</span>
          <span className="flex-1 text-gray-200 font-medium truncate">{p.name}</span>
          {p.goals > 0 && (
            <span className="text-xs text-gray-500 hidden sm:block">⚽ {p.goals}</span>
          )}
          <span className="font-bold text-white w-8 text-center">{p[valueKey]}</span>
          <div className="w-28 h-1.5 bg-surface-2 rounded-full overflow-hidden">
            <div
              className="h-full rounded-full"
              style={{ width: `${(p[valueKey] / (maxValue || 1)) * 100}%`, background: color }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

export default function Players() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  // Default to appearances: goal events are not in the SQL schema.
  const [tab, setTab] = useState('mostAppearances');
  const isMobile = useIsMobile();
  const { t } = useLanguage();
  const { has, note } = useCapabilities();

  useEffect(() => {
    api.players().then(setData).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="flex items-center justify-center h-64 text-gray-400">{t('loading')}</div>;
  if (!data)   return <div className="text-red-400">{t('failedToLoad')}</div>;

  const tabConfig = {
    topScorers:      { list: data.topScorers || [], valueKey: 'goals',  valueLabel: t('valueGoals'),     color: '#00A8E8' },
    mostAppearances: { list: data.mostAppearances, valueKey: 'starters', valueLabel: t('valueStarts'),    color: '#22c55e' },
    mostBench:       { list: data.mostBench,       valueKey: 'bench',    valueLabel: t('valueBench'),     color: '#f59e0b' },
    mostTotal:       { list: data.mostTotal,       valueKey: 'total',    valueLabel: t('valueSquadApps'), color: '#a855f7' },
  };

  const { list, valueKey, valueLabel, color } = tabConfig[tab];
  const chartData = list.slice(0, 15);
  const maxValue = list[0]?.[valueKey] || 1;

  return (
    <div className="space-y-6 max-w-5xl">
      <div>
        <h1 className="text-2xl font-bold text-white">{t('playersTitle')}</h1>
        <p className="text-gray-500 text-sm mt-0.5">{t('playersSubtitle')}</p>
      </div>

      {/* Tabs */}
      <div className="flex flex-wrap gap-2">
        {TABS
          .filter(tabItem => tabItem.key !== 'topScorers' || has('playerGoals'))
          .map(tabItem => (
            <button key={tabItem.key} onClick={() => setTab(tabItem.key)} className={`tab-btn ${tab === tabItem.key ? 'active' : ''}`}>
              {t(tabItem.labelKey)}
            </button>
          ))}
      </div>

      {/* Chart */}
      {tab === 'topScorers' && !has('playerGoals') ? (
        <NoData title={t('tabTopScorers')} note={note('playerGoals')} />
      ) : (
      <div className="card">
        <h3 className="text-sm font-semibold text-gray-300 mb-4">{t('topN', { label: valueLabel })}</h3>
        <ResponsiveContainer width="100%" height={320}>
          <BarChart data={chartData} layout="vertical" barSize={16} margin={{ top: 5, right: isMobile ? 28 : 5, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#30363D" horizontal={false} />
            <XAxis type="number" tick={{ fill: '#8B949E', fontSize: 11 }} axisLine={false} tickLine={false} />
            <YAxis dataKey="name" type="category" tick={{ fill: '#8B949E', fontSize: 11 }} axisLine={false} tickLine={false} width={130} />
            {!isMobile && <Tooltip content={<CustomTooltip />} />}
            <Bar dataKey={valueKey} name={valueLabel} fill={color} radius={[0, 4, 4, 0]}>
              {isMobile && <LabelList dataKey={valueKey} position="right" fontSize={10} fill="#8B949E" />}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      )}

      {/* Full table */}
      {tab === 'topScorers' && !has('playerGoals') ? null : (
      <div className="card">
        <h3 className="text-sm font-semibold text-gray-300 mb-4">{t('fullRankings', { label: valueLabel })}</h3>
        <PlayerTable players={list} valueKey={valueKey} maxValue={maxValue} color={color} />
      </div>
      )}
    </div>
  );
}
