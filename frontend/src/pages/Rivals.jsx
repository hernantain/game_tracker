import Crest from '../components/Crest';
import { useEffect, useState, useMemo } from 'react';
import { Search, ChevronUp, ChevronDown, ChevronsUpDown } from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, LabelList,
} from 'recharts';
import { useIsMobile } from '../hooks/useIsMobile';
import { useLanguage } from '../i18n/LanguageContext';
import { api } from '../api';

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-surface-1 border border-surface-3 rounded-lg p-3 text-sm shadow-xl">
      <p className="text-gray-400 mb-1">{label}</p>
      {payload.map(p => <p key={p.name} style={{ color: p.color }}>{p.name}: <b>{p.value}</b></p>)}
    </div>
  );
};

const COLS = [
  { key: 'rival',       labelKey: 'colOpponent',    align: 'text-left'  },
  { key: 'played',      labelKey: 'colPlayed',      align: 'text-center'},
  { key: 'wins',        labelKey: 'colWins',        align: 'text-center'},
  { key: 'draws',       labelKey: 'colDraws',       align: 'text-center'},
  { key: 'losses',      labelKey: 'colLosses',      align: 'text-center'},
  { key: 'goalsFor',    labelKey: 'colGoalsFor',    align: 'text-center'},
  { key: 'goalsAgainst',labelKey: 'colGoalsAgainst',align: 'text-center'},
  { key: 'goalDiff',    labelKey: 'colGoalDiff',    align: 'text-center'},
  { key: 'winRate',     labelKey: 'colWinRate',     align: 'text-center'},
];

function SortIcon({ col, sort }) {
  if (sort.key !== col) return <ChevronsUpDown size={12} className="text-gray-600" />;
  return sort.dir === 'asc' ? <ChevronUp size={12} className="text-racing-blue" /> : <ChevronDown size={12} className="text-racing-blue" />;
}

export default function Rivals() {
  const [rivals, setRivals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [sort, setSort] = useState({ key: 'played', dir: 'desc' });
  const [selected, setSelected] = useState(null);
  const isMobile = useIsMobile();
  const { t } = useLanguage();

  useEffect(() => {
    api.opponents().then(setRivals).finally(() => setLoading(false));
  }, []);

  const filtered = useMemo(() => {
    let list = rivals;
    if (search) list = list.filter(r => r.rival.toLowerCase().includes(search.toLowerCase()));
    return [...list].sort((a, b) => {
      const va = a[sort.key], vb = b[sort.key];
      if (typeof va === 'string') return sort.dir === 'asc' ? va.localeCompare(vb) : vb.localeCompare(va);
      return sort.dir === 'asc' ? va - vb : vb - va;
    });
  }, [rivals, search, sort]);

  const toggleSort = (key) => {
    setSort(s => s.key === key ? { key, dir: s.dir === 'asc' ? 'desc' : 'asc' } : { key, dir: 'desc' });
  };

  const mostPlayed = [...rivals].sort((a, b) => b.played - a.played).slice(0, 12);
  const bestRecord = [...rivals].filter(r => r.played >= 3).sort((a, b) => b.winRate - a.winRate).slice(0, 8);
  const worstRecord = [...rivals].filter(r => r.played >= 3).sort((a, b) => a.winRate - b.winRate).slice(0, 8);

  if (loading) return <div className="flex items-center justify-center h-64 text-gray-400">{t('loading')}</div>;

  return (
    <div className="space-y-6 max-w-6xl">
      <div>
        <h1 className="text-2xl font-bold text-white">{t('rivalsTitle')}</h1>
        <p className="text-gray-500 text-sm mt-0.5">{t('differentOpponents', { count: rivals.length })}</p>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="card">
          <h3 className="text-sm font-semibold text-gray-300 mb-4">{t('mostPlayedOpponents')}</h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={mostPlayed} layout="vertical" barSize={14}>
              <CartesianGrid strokeDasharray="3 3" stroke="#30363D" horizontal={false} />
              <XAxis type="number" tick={{ fill: '#8B949E', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis dataKey="rival" type="category" tick={{ fill: '#8B949E', fontSize: 11 }} axisLine={false} tickLine={false} width={90} />
              {!isMobile && <Tooltip content={<CustomTooltip />} />}
              <Bar dataKey="wins"   name={t('wins')}   stackId="a" fill="#22c55e">
                {isMobile && <LabelList dataKey="wins" position="center" fontSize={9} fill="#0D1117" />}
              </Bar>
              <Bar dataKey="draws"  name={t('draws')}  stackId="a" fill="#f59e0b">
                {isMobile && <LabelList dataKey="draws" position="center" fontSize={9} fill="#0D1117" />}
              </Bar>
              <Bar dataKey="losses" name={t('losses')} stackId="a" fill="#ef4444" radius={[0, 4, 4, 0]}>
                {isMobile && <LabelList dataKey="losses" position="center" fontSize={9} fill="#0D1117" />}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <h3 className="text-sm font-semibold text-gray-300 mb-4">{t('winRateVsOpponents')}</h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={bestRecord} layout="vertical" barSize={14} margin={{ top: 5, right: isMobile ? 34 : 5, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#30363D" horizontal={false} />
              <XAxis type="number" domain={[0, 100]} tick={{ fill: '#8B949E', fontSize: 11 }} axisLine={false} tickLine={false} unit="%" />
              <YAxis dataKey="rival" type="category" tick={{ fill: '#8B949E', fontSize: 11 }} axisLine={false} tickLine={false} width={90} />
              {!isMobile && <Tooltip content={<CustomTooltip />} formatter={(v) => [`${v}%`, t('statWinRateShort')]} />}
              <Bar dataKey="winRate" name={t('statWinRateShort')} radius={[0, 4, 4, 0]}>
                {bestRecord.map((entry, i) => <Cell key={i} fill={entry.winRate >= 60 ? '#22c55e' : entry.winRate >= 40 ? '#f59e0b' : '#ef4444'} />)}
                {isMobile && <LabelList dataKey="winRate" position="right" fontSize={10} fill="#8B949E" formatter={(v) => `${v}%`} />}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Selected rival detail */}
      {selected && (
        <div className="card border-racing-blue/40">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-white flex items-center gap-2 min-w-0">
              <Crest espnId={selected.espnTeamId} name={selected.rival} size={28} />
              <span className="truncate">vs {selected.rival}</span>
            </h3>
            <button onClick={() => setSelected(null)} className="text-gray-500 hover:text-white text-xs">{t('close')}</button>
          </div>
          <div className="flex flex-wrap gap-6 items-center">
            <div className="flex gap-6">
              <div className="text-center"><div className="text-2xl font-bold text-green-400">{selected.wins}</div><div className="text-xs text-gray-500">{t('wins')}</div></div>
              <div className="text-center"><div className="text-2xl font-bold text-yellow-400">{selected.draws}</div><div className="text-xs text-gray-500">{t('draws')}</div></div>
              <div className="text-center"><div className="text-2xl font-bold text-red-400">{selected.losses}</div><div className="text-xs text-gray-500">{t('losses')}</div></div>
              <div className="text-center"><div className="text-2xl font-bold text-racing-blue">{selected.goalsFor}</div><div className="text-xs text-gray-500">{t('goalsFor')}</div></div>
              <div className="text-center"><div className="text-2xl font-bold text-gray-300">{selected.goalsAgainst}</div><div className="text-xs text-gray-500">{t('goalsAgainst')}</div></div>
              <div className="text-center"><div className={`text-2xl font-bold ${selected.goalDiff > 0 ? 'text-green-400' : selected.goalDiff < 0 ? 'text-red-400' : 'text-gray-400'}`}>{selected.goalDiff > 0 ? '+' : ''}{selected.goalDiff}</div><div className="text-xs text-gray-500">{t('statGoalDiff')}</div></div>
              <div className="text-center"><div className="text-2xl font-bold text-white">{selected.winRate}%</div><div className="text-xs text-gray-500">{t('statWinRateShort')}</div></div>
            </div>
          </div>
        </div>
      )}

      {/* Table */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-gray-300">{t('allOpponents')}</h3>
          <div className="relative">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
            <input
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder={t('filterOpponent')}
              className="bg-surface-2 border border-surface-3 rounded-lg pl-8 pr-3 py-1.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-racing-blue w-52"
            />
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-surface-3">
                {COLS.map(c => (
                  <th
                    key={c.key}
                    onClick={() => toggleSort(c.key)}
                    className={`pb-2 text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:text-gray-300 select-none ${c.align}`}
                  >
                    <span className="inline-flex items-center gap-1">
                      {t(c.labelKey)} <SortIcon col={c.key} sort={sort} />
                    </span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.map(r => (
                <tr
                  key={r.rival}
                  onClick={() => setSelected(r.rival === selected?.rival ? null : r)}
                  className={`border-b border-surface-3/40 hover:bg-surface-2 cursor-pointer transition-colors ${r.rival === selected?.rival ? 'bg-racing-blue/10' : ''}`}
                >
                  <td className="py-2.5 font-medium text-white">
                    <span className="flex items-center gap-2">
                      <Crest espnId={r.espnTeamId} name={r.rival} size={22} />
                      <span className="truncate">{r.rival}</span>
                    </span>
                  </td>
                  <td className="py-2.5 text-center text-gray-400">{r.played}</td>
                  <td className="py-2.5 text-center text-green-400 font-medium">{r.wins}</td>
                  <td className="py-2.5 text-center text-yellow-400">{r.draws}</td>
                  <td className="py-2.5 text-center text-red-400">{r.losses}</td>
                  <td className="py-2.5 text-center text-gray-300">{r.goalsFor}</td>
                  <td className="py-2.5 text-center text-gray-400">{r.goalsAgainst}</td>
                  <td className={`py-2.5 text-center font-medium ${r.goalDiff > 0 ? 'text-green-400' : r.goalDiff < 0 ? 'text-red-400' : 'text-gray-400'}`}>
                    {r.goalDiff > 0 ? '+' : ''}{r.goalDiff}
                  </td>
                  <td className="py-2.5 text-center">
                    <span className={`text-xs font-bold px-1.5 py-0.5 rounded ${r.winRate >= 60 ? 'bg-green-900/60 text-green-400' : r.winRate >= 40 ? 'bg-yellow-900/60 text-yellow-400' : 'bg-red-900/60 text-red-400'}`}>
                      {r.winRate}%
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
