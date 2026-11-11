import { useEffect, useState } from 'react';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, AreaChart, Area, LabelList,
} from 'recharts';
import {
  Trophy, Target, Shield, Zap, TrendingUp, Award, CheckCircle, XCircle, Minus,
} from 'lucide-react';
import StatCard from '../components/StatCard';
import { useIsMobile } from '../hooks/useIsMobile';
import { useLanguage } from '../i18n/LanguageContext';
import { api } from '../api';
import NoData from '../components/NoData';
import Crest from '../components/Crest';
import { useCapabilities } from '../hooks/useCapabilities';

const COLORS = {
  win:  '#22c55e',
  draw: '#f59e0b',
  loss: '#ef4444',
  blue: '#00A8E8',
  blue2:'#33BBEF',
};

// Legacy sent five competition types; the SQL model has two, keyed by who
// organises the competition. Both key sets are kept so --legacy still colours.
const TYPE_COLORS = {
  national:      '#00A8E8',
  international: '#f59e0b',
  Liga:          '#00A8E8',
  'Copa Local':  '#a855f7',
  Libertadores:  '#f59e0b',
  Sudamericana:  '#22c55e',
  Recopa:        '#ec4899',
};

const TYPE_NAME_KEYS = {
  national:      'typeNational',
  international: 'typeInternational',
  Liga:         'typeLeague',
  'Copa Local': 'typeCup',
  Libertadores: 'typeLibertadores',
  Sudamericana: 'typeSudamericana',
  Recopa:       'typeRecopa',
};

function FormDot({ result, t }) {
  if (result === 'W') return <span title={t('win')}  className="w-7 h-7 rounded-full bg-green-500 flex items-center justify-center text-white text-xs font-bold">W</span>;
  if (result === 'D') return <span title={t('draw')} className="w-7 h-7 rounded-full bg-yellow-500 flex items-center justify-center text-white text-xs font-bold">D</span>;
  return                     <span title={t('loss')} className="w-7 h-7 rounded-full bg-red-500   flex items-center justify-center text-white text-xs font-bold">L</span>;
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-surface-1 border border-surface-3 rounded-lg p-3 text-sm shadow-xl">
      <p className="text-gray-400 mb-1">{label}</p>
      {payload.map(p => (
        <p key={p.name} style={{ color: p.color }}>
          {p.name}: <span className="font-bold">{p.value}</span>
        </p>
      ))}
    </div>
  );
};

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const isMobile = useIsMobile();
  const { t } = useLanguage();
  const { has, note } = useCapabilities();

  useEffect(() => {
    api.statistics().then(setData).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="flex items-center justify-center h-64 text-gray-400">{t('loading')}</div>;
  if (!data)   return <div className="text-red-400">{t('failedToLoad')}</div>;

  // byType / goalsByMinute / topScorers exist only in legacy mode: the SQL
  // schema models no competitions and no goal events. Defaulted so the page
  // renders either way; /api/capabilities decides what to show.
  const {
    stats, byYear, recentMatches, form,
    byType = [], goalsByMinute = [], topScorers = [],
  } = data;

  const wdlData = [
    { name: t('wins'),   value: stats.wins,   fill: COLORS.win  },
    { name: t('draws'),  value: stats.draws,  fill: COLORS.draw },
    { name: t('losses'), value: stats.losses, fill: COLORS.loss },
  ];

  const byTypeTranslated = (byType || []).map(d => {
    const key = TYPE_NAME_KEYS[d.type] || TYPE_NAME_KEYS[d.name];
    return { ...d, name: key ? t(key) : d.name };
  });

  return (
    <div className="space-y-6 max-w-7xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">{t('dashboardTitle')}</h1>
          <p className="text-gray-500 text-sm mt-0.5">{t('dashboardSubtitle')}</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500">{t('currentForm')}</span>
          <div className="flex gap-1">
            {[...form].reverse().map((r, i) => <FormDot key={i} result={r} t={t} />)}
          </div>
        </div>
      </div>

      {/* Key stats row 1 */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        <StatCard label={t('statTotalGames')}    value={stats.totalGames}  icon={Target}    />
        <StatCard label={t('statWinRate')}       value={`${stats.winRate}%`} icon={TrendingUp} accent />
        <StatCard label={t('statGoalsScored')}   value={stats.goalsScored} icon={Zap}       />
        <StatCard label={t('statGoalsConceded')} value={stats.goalsConceded} icon={Shield}  />
        <StatCard label={t('statCleanSheets')}   value={stats.cleanSheets} icon={CheckCircle} />
      </div>

      {/* Key stats row 2 */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        <StatCard label={t('wins')}          value={stats.wins}         sub={t('pctOfGames', { pct: Math.round(stats.wins/stats.totalGames*100) })} />
        <StatCard label={t('draws')}         value={stats.draws}        sub={t('pctOfGames', { pct: Math.round(stats.draws/stats.totalGames*100) })} />
        <StatCard label={t('losses')}        value={stats.losses}       sub={t('pctOfGames', { pct: Math.round(stats.losses/stats.totalGames*100) })} />
        <StatCard label={t('statGoalDiff')}  value={(stats.goalDifference > 0 ? '+' : '') + stats.goalDifference} accent={stats.goalDifference > 0} />
        <StatCard label={t('statAvgGoals')}  value={stats.avgGoalsScored} sub={t('concededAvg', { val: stats.avgGoalsConceded })} />
      </div>

      {/* Charts row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Goals by year area chart */}
        <div className="card lg:col-span-2">
          <h3 className="text-sm font-semibold text-gray-300 mb-4">{t('chartGoalsPerYear')}</h3>
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={byYear}>
              <defs>
                <linearGradient id="gradScored" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={COLORS.blue} stopOpacity={0.3} />
                  <stop offset="95%" stopColor={COLORS.blue} stopOpacity={0} />
                </linearGradient>
                <linearGradient id="gradConceded" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={COLORS.loss} stopOpacity={0.3} />
                  <stop offset="95%" stopColor={COLORS.loss} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#30363D" />
              <XAxis dataKey="year" tick={{ fill: '#8B949E', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#8B949E', fontSize: 11 }} axisLine={false} tickLine={false} />
              {!isMobile && <Tooltip content={<CustomTooltip />} />}
              <Legend wrapperStyle={{ fontSize: 12, color: '#8B949E' }} />
              <Area type="monotone" dataKey="goalsScored"   name={t('seriesScored')}   stroke={COLORS.blue} fill="url(#gradScored)"    strokeWidth={2}>
                {isMobile && <LabelList dataKey="goalsScored" position="top" fontSize={9} fill={COLORS.blue} />}
              </Area>
              <Area type="monotone" dataKey="goalsConceded" name={t('seriesConceded')} stroke={COLORS.loss} fill="url(#gradConceded)"  strokeWidth={2}>
                {isMobile && <LabelList dataKey="goalsConceded" position="bottom" fontSize={9} fill={COLORS.loss} />}
              </Area>
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* W/D/L Pie */}
        <div className="card">
          <h3 className="text-sm font-semibold text-gray-300 mb-4">{t('chartResultDistribution')}</h3>
          <ResponsiveContainer width="100%" height={180}>
            <PieChart>
              <Pie data={wdlData} cx="50%" cy="50%" innerRadius={50} outerRadius={75} paddingAngle={3} dataKey="value"
                label={isMobile ? ({ value }) => value : false} labelLine={false}
              >
                {wdlData.map((entry, i) => <Cell key={i} fill={entry.fill} />)}
              </Pie>
              {!isMobile && <Tooltip formatter={(v, n) => [`${v} ${t('games')}`, n]} contentStyle={{ background: '#161B22', border: '1px solid #30363D', borderRadius: 8 }} />}
            </PieChart>
          </ResponsiveContainer>
          <div className="flex justify-center gap-4 mt-1">
            {wdlData.map(d => (
              <div key={d.name} className="flex items-center gap-1.5 text-xs">
                <span className="w-2.5 h-2.5 rounded-full" style={{ background: d.fill }} />
                <span className="text-gray-400">{d.name} <span className="text-white font-bold">{d.value}</span></span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Charts row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Wins/Draws/Losses by year */}
        <div className="card">
          <h3 className="text-sm font-semibold text-gray-300 mb-4">{t('chartResultsByYear')}</h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={byYear} barSize={8}>
              <CartesianGrid strokeDasharray="3 3" stroke="#30363D" />
              <XAxis dataKey="year" tick={{ fill: '#8B949E', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#8B949E', fontSize: 11 }} axisLine={false} tickLine={false} />
              {!isMobile && <Tooltip content={<CustomTooltip />} />}
              <Legend wrapperStyle={{ fontSize: 12, color: '#8B949E' }} />
              <Bar dataKey="wins"   name={t('wins')}   fill={COLORS.win}  radius={[4, 4, 0, 0]}>
                {isMobile && <LabelList dataKey="wins" position="top" fontSize={8} fill={COLORS.win} />}
              </Bar>
              <Bar dataKey="draws"  name={t('draws')}  fill={COLORS.draw} radius={[4, 4, 0, 0]}>
                {isMobile && <LabelList dataKey="draws" position="top" fontSize={8} fill={COLORS.draw} />}
              </Bar>
              <Bar dataKey="losses" name={t('losses')} fill={COLORS.loss} radius={[4, 4, 0, 0]}>
                {isMobile && <LabelList dataKey="losses" position="top" fontSize={8} fill={COLORS.loss} />}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Performance by competition type -- needs competition data */}
        {!has('tournaments') ? (
          <NoData title={t('chartPerformanceByCompetition')} note={note('tournaments')} />
        ) : (
        <div className="card">
          <h3 className="text-sm font-semibold text-gray-300 mb-4">{t('chartPerformanceByCompetition')}</h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={byTypeTranslated} layout="vertical" barSize={12}>
              <CartesianGrid strokeDasharray="3 3" stroke="#30363D" horizontal={false} />
              <XAxis type="number" tick={{ fill: '#8B949E', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis dataKey="name" type="category" tick={{ fill: '#8B949E', fontSize: 11 }} axisLine={false} tickLine={false} width={90} />
              {!isMobile && <Tooltip content={<CustomTooltip />} />}
              <Legend wrapperStyle={{ fontSize: 12, color: '#8B949E' }} />
              <Bar dataKey="wins"   name={t('wins')}   fill={COLORS.win}  radius={[0, 4, 4, 0]} stackId="a">
                {isMobile && <LabelList dataKey="wins" position="center" fontSize={9} fill="#0D1117" />}
              </Bar>
              <Bar dataKey="draws"  name={t('draws')}  fill={COLORS.draw} radius={[0, 0, 0, 0]} stackId="a">
                {isMobile && <LabelList dataKey="draws" position="center" fontSize={9} fill="#0D1117" />}
              </Bar>
              <Bar dataKey="losses" name={t('losses')} fill={COLORS.loss} radius={[0, 4, 4, 0]} stackId="a">
                {isMobile && <LabelList dataKey="losses" position="center" fontSize={9} fill="#0D1117" />}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
        )}
      </div>

      {/* Charts row 3 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Top scorers -- needs goal events */}
        {!has('playerGoals') ? (
          <NoData title={t('chartTopScorers')} note={note('playerGoals')} />
        ) : (
        <div className="card">
          <h3 className="text-sm font-semibold text-gray-300 mb-4">{t('chartTopScorers')}</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={topScorers} layout="vertical" barSize={14} margin={{ top: 5, right: isMobile ? 28 : 5, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#30363D" horizontal={false} />
              <XAxis type="number" tick={{ fill: '#8B949E', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis dataKey="name" type="category" tick={{ fill: '#8B949E', fontSize: 11 }} axisLine={false} tickLine={false} width={130} />
              {!isMobile && <Tooltip content={<CustomTooltip />} />}
              <Bar dataKey="goals" name={t('goals')} fill={COLORS.blue} radius={[0, 4, 4, 0]}>
                {isMobile && <LabelList dataKey="goals" position="right" fontSize={10} fill="#8B949E" />}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        )}

        {/* Goals by minute -- needs per-goal minutes */}
        {!has('goalMinutes') ? (
          <NoData title={t('chartGoalsByMinute')} note={note('goalMinutes')} />
        ) : (
        <div className="card">
          <h3 className="text-sm font-semibold text-gray-300 mb-4">{t('chartGoalsByMinute')}</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={goalsByMinute} barSize={32}>
              <CartesianGrid strokeDasharray="3 3" stroke="#30363D" />
              <XAxis dataKey="range" tick={{ fill: '#8B949E', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#8B949E', fontSize: 11 }} axisLine={false} tickLine={false} />
              {!isMobile && <Tooltip content={<CustomTooltip />} />}
              <Bar dataKey="goals" name={t('goals')} fill={COLORS.blue} radius={[4, 4, 0, 0]}>
                {isMobile && <LabelList dataKey="goals" position="top" fontSize={10} fill="#8B949E" />}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
        )}
      </div>

      {/* Highlights */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.biggestWin && (
          <div className="card border-green-900/60">
            <div className="text-xs text-gray-500 uppercase tracking-wider mb-2">{t('biggestWin')}</div>
            <div className="text-green-400 font-bold text-xl">{stats.biggestWin.localScore}–{stats.biggestWin.rivalScore}</div>
            <div className="text-white font-medium flex items-center gap-2">
              <Crest espnId={stats.biggestWin.rivalEspnId} name={stats.biggestWin.rival} size={20} />
              <span className="truncate">vs {stats.biggestWin.rival}</span>
            </div>
            <div className="text-xs text-gray-500 mt-1">{stats.biggestWin.tournament}</div>
            <div className="text-xs text-gray-600">{stats.biggestWin.date}</div>
          </div>
        )}
        {stats.biggestLoss && (
          <div className="card border-red-900/60">
            <div className="text-xs text-gray-500 uppercase tracking-wider mb-2">{t('biggestLoss')}</div>
            <div className="text-red-400 font-bold text-xl">{stats.biggestLoss.localScore}–{stats.biggestLoss.rivalScore}</div>
            <div className="text-white font-medium flex items-center gap-2">
              <Crest espnId={stats.biggestLoss.rivalEspnId} name={stats.biggestLoss.rival} size={20} />
              <span className="truncate">vs {stats.biggestLoss.rival}</span>
            </div>
            <div className="text-xs text-gray-500 mt-1">{stats.biggestLoss.tournament}</div>
            <div className="text-xs text-gray-600">{stats.biggestLoss.date}</div>
          </div>
        )}
        <div className="card">
          <div className="text-xs text-gray-500 uppercase tracking-wider mb-2">{t('bestWinStreak')}</div>
          <div className="text-racing-blue font-bold text-3xl">{stats.maxWinStreak}</div>
          <div className="text-gray-400 text-sm">{t('consecutiveWins')}</div>
        </div>
        <div className="card">
          <div className="text-xs text-gray-500 uppercase tracking-wider mb-2">{t('bestUnbeatenRun')}</div>
          <div className="text-racing-blue font-bold text-3xl">{stats.maxUnbeaten}</div>
          <div className="text-gray-400 text-sm">{t('gamesWithoutLosing')}</div>
        </div>
      </div>

      {/* Recent matches */}
      <div className="card">
        <h3 className="text-sm font-semibold text-gray-300 mb-4">{t('recentMatches')}</h3>
        <div className="space-y-1">
          {recentMatches.map((m, i) => (
            <div key={i} className="flex items-center gap-4 px-3 py-2.5 rounded-lg hover:bg-surface-2 transition-colors">
              <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                m.result === 'W' ? 'bg-green-500' : m.result === 'D' ? 'bg-yellow-500' : 'bg-red-500'
              } text-white`}>{m.result}</span>
              <span className="flex-1 flex items-center gap-2 min-w-0">
                <Crest espnId={m.rivalEspnId} name={m.rival} size={22} />
                <span className="font-medium text-white truncate">{m.rival}</span>
              </span>
              <span className="font-mono font-bold text-lg">
                <span className={m.localScore > m.rivalScore ? 'text-green-400' : m.localScore < m.rivalScore ? 'text-red-400' : 'text-yellow-400'}>
                  {m.localScore}
                </span>
                <span className="text-gray-600">–</span>
                <span className="text-gray-300">{m.rivalScore}</span>
              </span>
              {m.goals?.length > 0 && (
                <span className="hidden md:block text-xs text-gray-500 max-w-[160px] truncate">
                  ⚽ {m.goals.map(g => g.name).join(', ')}
                </span>
              )}
              <span className="hidden lg:block text-xs text-gray-500 text-right w-40">
                <div>{m.tournament}</div>
                <div>{m.date}</div>
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
