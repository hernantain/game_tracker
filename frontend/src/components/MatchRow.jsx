import Crest from './Crest';

function ResultBadge({ result }) {
  if (result === 'W') return <span className="badge-w">W</span>;
  if (result === 'D') return <span className="badge-d">D</span>;
  return <span className="badge-l">L</span>;
}

export default function MatchRow({ match }) {
  const {
    rival, localScore, rivalScore, date, result, goals, fase,
    // The SQL app sends `competition` + `opponentEspnId`; the legacy JSON app
    // sends `tournamentName` and no crest key.
    tournamentName, competition, opponentEspnId,
  } = match;
  const scorerList = goals?.map(g => g.name).join(', ') || '—';

  return (
    <div className="flex items-center gap-4 px-4 py-3 rounded-lg hover:bg-surface-2 transition-colors border border-transparent hover:border-surface-3 group">
      <ResultBadge result={result} />

      <div className="flex items-center gap-2 min-w-0 flex-1">
        <Crest espnId={opponentEspnId} name={rival} size={24} />
        <span className="font-semibold text-white truncate">{rival}</span>
        {fase && (
          <span className="text-xs text-gray-500 border border-surface-3 px-1.5 py-0.5 rounded hidden sm:inline">
            {fase}
          </span>
        )}
      </div>

      <div className="flex items-center gap-1 font-mono font-bold text-lg">
        <span className={localScore > rivalScore ? 'text-green-400' : localScore < rivalScore ? 'text-red-400' : 'text-yellow-400'}>
          {localScore}
        </span>
        <span className="text-gray-600">–</span>
        <span className="text-gray-300">{rivalScore}</span>
      </div>

      <div className="hidden md:block text-xs text-gray-500 w-28 text-right truncate" title={scorerList}>
        {goals?.length > 0 ? `⚽ ${scorerList}` : ''}
      </div>

      <div className="hidden lg:block text-xs text-gray-500 w-36 text-right">
        <div>{tournamentName || competition}</div>
        <div>{date}</div>
      </div>
    </div>
  );
}
