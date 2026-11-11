import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Trophy, ChevronRight } from 'lucide-react';
import { useLanguage } from '../i18n/LanguageContext';
import { api, isLegacy } from '../api';
import NoData from '../components/NoData';
import { useCapabilities } from '../hooks/useCapabilities';

// SQL model: two types, keyed by organiser. Legacy's five are kept so
// --legacy still renders its own tournament list.
const TYPE_META = {
  national:      { key: 'typeNational',      color: 'bg-blue-900/40 text-blue-400 border-blue-800'    },
  international: { key: 'typeInternational', color: 'bg-yellow-900/40 text-yellow-400 border-yellow-800' },
  league:       { key: 'typeLeague',         color: 'bg-blue-900/40 text-blue-400 border-blue-800'    },
  cup:          { key: 'typeCup',            color: 'bg-purple-900/40 text-purple-400 border-purple-800' },
  libertadores: { key: 'typeLibertadores',   color: 'bg-yellow-900/40 text-yellow-400 border-yellow-800' },
  sudamericana: { key: 'typeSudamericana',   color: 'bg-green-900/40 text-green-400 border-green-800'  },
  recopa:       { key: 'typeRecopa',         color: 'bg-pink-900/40 text-pink-400 border-pink-800'     },
};

const LEGACY_TABS = [
  { key: 'all',          labelKey: 'all'               },
  { key: 'league',       labelKey: 'typeLeague'         },
  { key: 'cup',          labelKey: 'typeCup'            },
  { key: 'libertadores', labelKey: 'typeLibertadores'   },
  { key: 'sudamericana', labelKey: 'typeSudamericana'   },
  { key: 'recopa',       labelKey: 'typeRecopa'         },
];
const SQL_TABS = [
  { key: 'all',           labelKey: 'all'               },
  { key: 'national',      labelKey: 'typeNational'      },
  { key: 'international', labelKey: 'typeInternational' },
];

function ResultBar({ wins, draws, losses, total }) {
  const wp = (wins / total) * 100;
  const dp = (draws / total) * 100;
  const lp = (losses / total) * 100;
  return (
    <div className="h-2 w-full rounded-full overflow-hidden flex gap-px">
      <div className="bg-green-500 rounded-l" style={{ width: `${wp}%` }} />
      <div className="bg-yellow-500"          style={{ width: `${dp}%` }} />
      <div className="bg-red-500 rounded-r"   style={{ width: `${lp}%` }} />
    </div>
  );
}

export default function Tournaments() {
  const [list, setList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState('all');
  const { t } = useLanguage();
  const { has, note } = useCapabilities();

  useEffect(() => {
    api.tournaments().then(setList).catch(() => setList([])).finally(() => setLoading(false));
  }, []);

  const filtered = tab === 'all' ? list : list.filter(item => item.type === tab);

  if (loading) return <div className="flex items-center justify-center h-64 text-gray-400">{t('loading')}</div>;

  // Competitions are not modelled in SQL, so the whole page has no source.
  if (!has('tournaments')) {
    return (
      <div className="space-y-5 max-w-3xl">
        <h1 className="text-2xl font-bold text-white">{t('tournamentsTitle')}</h1>
        <NoData note={note('tournaments')} />
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-7xl">
      <div>
        <h1 className="text-2xl font-bold text-white">{t('tournamentsTitle')}</h1>
        <p className="text-gray-500 text-sm mt-0.5">{t('tournamentsSubtitle', { count: list.length })}</p>
      </div>

      {/* Tabs */}
      <div className="flex flex-wrap gap-2">
        {(isLegacy ? LEGACY_TABS : SQL_TABS).map(tabItem => (
          <button key={tabItem.key} onClick={() => setTab(tabItem.key)} className={`tab-btn ${tab === tabItem.key ? 'active' : ''}`}>
            {t(tabItem.labelKey)}
            <span className="ml-1.5 text-xs opacity-70">
              {tabItem.key === 'all' ? list.length : list.filter(x => x.type === tabItem.key).length}
            </span>
          </button>
        ))}
      </div>

      {/* Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {filtered.map(item => {
          const meta = TYPE_META[item.type];
          const typeLabel = meta ? t(meta.key) : item.type;
          const typeColor = meta ? meta.color : 'bg-gray-800 text-gray-400 border-gray-700';
          return (
            <Link
              key={item.id}
              to={`/tournaments/${item.id}`}
              className="card hover:border-racing-blue/50 hover:bg-surface-2/50 transition-all duration-150 group"
            >
              <div className="flex items-start justify-between mb-3">
                <div>
                  <div className="font-semibold text-white group-hover:text-racing-blue transition-colors">{item.name}</div>
                  <span className={`mt-1 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${typeColor}`}>
                    {typeLabel}
                  </span>
                </div>
                <ChevronRight size={16} className="text-gray-600 group-hover:text-racing-blue mt-1 transition-colors" />
              </div>

              {/* W/D/L bar */}
              <ResultBar wins={item.wins} draws={item.draws} losses={item.losses} total={item.totalGames} />

              {/* Stats */}
              <div className="mt-3 grid grid-cols-3 gap-2 text-center">
                <div>
                  <div className="text-green-400 font-bold text-lg">{item.wins}</div>
                  <div className="text-xs text-gray-500">{t('wins')}</div>
                </div>
                <div>
                  <div className="text-yellow-400 font-bold text-lg">{item.draws}</div>
                  <div className="text-xs text-gray-500">{t('draws')}</div>
                </div>
                <div>
                  <div className="text-red-400 font-bold text-lg">{item.losses}</div>
                  <div className="text-xs text-gray-500">{t('losses')}</div>
                </div>
              </div>

              <div className="mt-3 pt-3 border-t border-surface-3 flex justify-between text-xs text-gray-500">
                <span>{t('gamesCount', { count: item.totalGames })}</span>
                <span>{t('scoredConceded', { scored: item.goalsScored, conceded: item.goalsConceded })}</span>
                <span className="font-medium text-white">{t('winRateAbbr', { pct: item.winRate })}</span>
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
