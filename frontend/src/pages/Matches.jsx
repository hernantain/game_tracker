import { useEffect, useState, useCallback } from 'react';
import { Search, Filter } from 'lucide-react';
import MatchRow from '../components/MatchRow';
import { useLanguage } from '../i18n/LanguageContext';
import { api, isLegacy } from '../api';
import { useCapabilities } from '../hooks/useCapabilities';

const RESULTS = [
  { key: '',  labelKey: 'all'    },
  { key: 'W', labelKey: 'wins'   },
  { key: 'D', labelKey: 'draws'  },
  { key: 'L', labelKey: 'losses' },
];

const LEGACY_TYPES = [
  { key: '',             labelKey: 'allTypes'          },
  { key: 'league',       labelKey: 'typeLeague'        },
  { key: 'cup',          labelKey: 'typeCup'           },
  { key: 'libertadores', labelKey: 'typeLibertadores'  },
  { key: 'sudamericana', labelKey: 'typeSudamericana'  },
  { key: 'recopa',       labelKey: 'typeRecopa'        },
];
const SQL_TYPES = [
  { key: '',              labelKey: 'allTypes'          },
  { key: 'national',      labelKey: 'typeNational'      },
  { key: 'international', labelKey: 'typeInternational' },
];
const TYPES = isLegacy ? LEGACY_TYPES : SQL_TYPES;

const PAGE_SIZE = 30;

export default function Matches() {
  const [matches, setMatches] = useState([]);
  const [tournaments, setTournaments] = useState([]);
  const [years, setYears] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({ search: '', result: '', tournament: '', year: '', type: '' });
  const [page, setPage] = useState(1);
  const { t } = useLanguage();
  const { has } = useCapabilities();

  const loadMatches = useCallback(async () => {
    setLoading(true);
    const params = {};
    if (filters.search)     params.search     = filters.search;
    if (filters.result)     params.result     = filters.result;
    if (filters.year)       params.year       = filters.year;
    // The two backends name these differently.
    if (filters.tournament) {
      if (isLegacy) params.tournament = filters.tournament;
      else          params.competition = filters.tournament;
    }
    if (filters.type) {
      if (isLegacy) params.type = filters.type;
      else          params.competitionType = filters.type;
    }
    const data = await api.games(params);
    setMatches(data);
    setPage(1);
    setLoading(false);
  }, [filters]);

  useEffect(() => { loadMatches(); }, [loadMatches]);
  useEffect(() => {
    // Returns [] in SQL mode: competitions are not modelled yet.
    api.tournaments().then(setTournaments).catch(() => setTournaments([]));
    api.seasons().then(setYears).catch(() => setYears([]));
  }, []);

  const setFilter = (key, val) => {
    setFilters(f => ({ ...f, [key]: val, ...(key === 'type' ? { tournament: '' } : {}) }));
  };

  const paged = matches.slice(0, page * PAGE_SIZE);
  const hasMore = paged.length < matches.length;

  const filteredTournaments = filters.type
    ? tournaments.filter(tr => tr.type === filters.type)
    : tournaments;

  return (
    <div className="space-y-5 max-w-5xl">
      <div>
        <h1 className="text-2xl font-bold text-white">{t('matchesTitle')}</h1>
        <p className="text-gray-500 text-sm mt-0.5">
          {loading ? t('loading') : t('matchesFound', { count: matches.length })}
        </p>
      </div>

      {/* Filters */}
      <div className="card space-y-3">
        {/* Search */}
        <div className="relative">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
          <input
            type="text"
            placeholder={t('searchOpponent')}
            value={filters.search}
            onChange={e => setFilter('search', e.target.value)}
            className="w-full bg-surface-2 border border-surface-3 rounded-lg pl-9 pr-4 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-racing-blue"
          />
        </div>

        <div className="flex flex-wrap gap-2">
          {/* Result filter */}
          <div className="flex gap-1">
            {RESULTS.map(r => (
              <button key={r.key} onClick={() => setFilter('result', r.key)}
                className={`tab-btn py-1.5 text-xs ${filters.result === r.key ? 'active' : ''}`}>
                {t(r.labelKey)}
              </button>
            ))}
          </div>

          {/* Type filter */}
          {/* Competition filters need tournament data, which SQL lacks. */}
          {has('tournaments') && (
            <>
              <select
                value={filters.type}
                onChange={e => setFilter('type', e.target.value)}
                className="bg-surface-2 border border-surface-3 rounded-lg px-3 py-1.5 text-sm text-gray-300 focus:outline-none focus:border-racing-blue"
              >
                {TYPES.map(opt => <option key={opt.key} value={opt.key}>{t(opt.labelKey)}</option>)}
              </select>

              <select
                value={filters.tournament}
                onChange={e => setFilter('tournament', e.target.value)}
                className="bg-surface-2 border border-surface-3 rounded-lg px-3 py-1.5 text-sm text-gray-300 focus:outline-none focus:border-racing-blue max-w-[200px]"
              >
                <option value="">{t('allCompetitions')}</option>
                {filteredTournaments.map(tr => <option key={tr.id} value={tr.id}>{tr.name}</option>)}
              </select>
            </>
          )}

          {/* Year filter */}
          <select
            value={filters.year}
            onChange={e => setFilter('year', e.target.value)}
            className="bg-surface-2 border border-surface-3 rounded-lg px-3 py-1.5 text-sm text-gray-300 focus:outline-none focus:border-racing-blue"
          >
            <option value="">{t('allYears')}</option>
            {years.map(y => <option key={y} value={y}>{y}</option>)}
          </select>
        </div>
      </div>

      {/* Match list */}
      <div className="card">
        {loading ? (
          <div className="text-center text-gray-500 py-12">{t('loading')}</div>
        ) : matches.length === 0 ? (
          <div className="text-center text-gray-500 py-12">{t('noMatchesFound')}</div>
        ) : (
          <>
            <div className="space-y-0.5">
              {paged.map((m, i) => <MatchRow key={i} match={m} />)}
            </div>
            {hasMore && (
              <button
                onClick={() => setPage(p => p + 1)}
                className="mt-4 w-full py-2 text-sm text-gray-400 hover:text-white border border-surface-3 hover:border-racing-blue rounded-lg transition-colors"
              >
                {t('loadMore', { count: matches.length - paged.length })}
              </button>
            )}
          </>
        )}
      </div>
    </div>
  );
}
