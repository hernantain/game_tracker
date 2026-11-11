import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LabelList,
} from 'recharts';
import MatchRow from '../components/MatchRow';
import { useIsMobile } from '../hooks/useIsMobile';
import { useLanguage } from '../i18n/LanguageContext';
import { api } from '../api';

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-surface-1 border border-surface-3 rounded-lg p-3 text-sm shadow-xl">
      <p className="text-gray-400 mb-1">{label}</p>
      {payload.map(p => (
        <p key={p.name} style={{ color: p.color }}>{p.name}: <b>{p.value}</b></p>
      ))}
    </div>
  );
};

function StatPill({ label, value, color = 'text-white' }) {
  return (
    <div className="card text-center">
      <div className={`text-2xl font-bold ${color}`}>{value}</div>
      <div className="text-xs text-gray-500 mt-1">{label}</div>
    </div>
  );
}

export default function TournamentDetail() {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const isMobile = useIsMobile();
  const { t } = useLanguage();

  useEffect(() => {
    api.tournament(id).then(setData).finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="flex items-center justify-center h-64 text-gray-400">{t('loading')}</div>;
  if (!data)   return <div className="text-red-400">{t('tournamentNotFound')}</div>;

  const { name, stats, matches, topScorers = [], playerStats = [] } = data;

  return (
    <div className="space-y-6 max-w-5xl">
      <div className="flex items-center gap-3">
        <Link to="/tournaments" className="text-gray-400 hover:text-white transition-colors">
          <ArrowLeft size={20} />
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-white">{name}</h1>
          <p className="text-gray-500 text-sm">{t('matchesPlayed', { count: stats.totalGames })}</p>
        </div>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
        <StatPill label={t('wins')}            value={stats.wins}          color="text-green-400"  />
        <StatPill label={t('draws')}           value={stats.draws}         color="text-yellow-400" />
        <StatPill label={t('losses')}          value={stats.losses}        color="text-red-400"    />
        <StatPill label={t('statScored')}      value={stats.goalsScored}   color="text-racing-blue"/>
        <StatPill label={t('statConceded')}    value={stats.goalsConceded} />
        <StatPill label={t('statWinRateShort')} value={`${stats.winRate}%`} color="text-racing-blue"/>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Scorers chart */}
        {topScorers.length > 0 && (
          <div className="card">
            <h3 className="text-sm font-semibold text-gray-300 mb-4">{t('tabTopScorers')}</h3>
            <ResponsiveContainer width="100%" height={Math.max(topScorers.length * 28, 160)}>
              <BarChart data={topScorers.slice(0, 10)} layout="vertical" barSize={12} margin={{ top: 5, right: isMobile ? 28 : 5, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#30363D" horizontal={false} />
                <XAxis type="number" tick={{ fill: '#8B949E', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis dataKey="name" type="category" tick={{ fill: '#8B949E', fontSize: 11 }} axisLine={false} tickLine={false} width={120} />
                {!isMobile && <Tooltip content={<CustomTooltip />} />}
                <Bar dataKey="goals" name={t('goals')} fill="#00A8E8" radius={[0, 4, 4, 0]}>
                  {isMobile && <LabelList dataKey="goals" position="right" fontSize={10} fill="#8B949E" />}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Player appearances */}
        <div className="card">
          <h3 className="text-sm font-semibold text-gray-300 mb-3">{t('mostUsedPlayers')}</h3>
          <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
            {playerStats.map((p, i) => (
              <div key={p.name} className="flex items-center gap-3 text-sm">
                <span className="text-gray-600 w-5 text-right text-xs">{i + 1}</span>
                <span className="flex-1 text-gray-300 truncate">{p.name}</span>
                <span className="text-white font-medium w-6 text-center">{p.starters}</span>
                <div className="w-24 h-1.5 bg-surface-2 rounded-full overflow-hidden">
                  <div className="h-full bg-racing-blue rounded-full" style={{ width: `${(p.starters / (playerStats[0]?.starters || 1)) * 100}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Match list */}
      <div className="card">
        <h3 className="text-sm font-semibold text-gray-300 mb-3">{t('allMatches')}</h3>
        <div className="space-y-0.5">
          {[...matches].reverse().map((m, i) => (
            <MatchRow key={i} match={m} />
          ))}
        </div>
      </div>
    </div>
  );
}
