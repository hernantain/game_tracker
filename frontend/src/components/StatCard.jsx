export default function StatCard({ label, value, sub, accent, icon: Icon, trend }) {
  return (
    <div className="card flex flex-col gap-2 hover:border-surface-3/80 transition-colors">
      <div className="flex items-start justify-between">
        <span className="text-xs font-medium text-gray-500 uppercase tracking-wider">{label}</span>
        {Icon && (
          <span className={`p-1.5 rounded-lg ${accent ? 'bg-racing-blue/10 text-racing-blue' : 'bg-surface-2 text-gray-400'}`}>
            <Icon size={14} />
          </span>
        )}
      </div>
      <div className={`text-3xl font-bold leading-none ${accent ? 'text-racing-blue' : 'text-white'}`}>
        {value}
      </div>
      {sub && <div className="text-xs text-gray-500">{sub}</div>}
    </div>
  );
}
