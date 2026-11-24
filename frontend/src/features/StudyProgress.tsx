import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import type { E } from '../model';

/** Progress from actual student enrollments, not illustrative metrics. */
export function StudyProgress({ items }: { items: E[] }) {
  const data = items.filter(item => item.status === 'active').slice(0, 8).map(item => ({
    name: item.course.title.length > 24 ? item.course.title.slice(0, 21) + '…' : item.course.title,
    percentual: Math.max(0, Math.min(100, item.progress_percent)),
  }));
  if (data.length === 0) return null;

  return <section className="lp-progress" aria-label="Resumo do seu progresso">
    <div className="lp-progress__heading">
      <h2>Seu progresso nos cursos</h2>
      <p>Percentual concluído, atualizado conforme as aulas realizadas.</p>
    </div>
    <div className="lp-progress__chart" role="img" aria-label={data.map(x => `${x.name}: ${x.percentual}% concluído`).join('; ')}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 14, right: 12, left: -18, bottom: 4 }}>
          <CartesianGrid strokeDasharray="3 5" vertical={false} stroke="var(--line)"/>
          <XAxis dataKey="name" tick={{ fill: 'var(--muted)', fontSize: 11 }} axisLine={false} tickLine={false} interval={0} angle={-15} textAnchor="end" height={65}/>
          <YAxis domain={[0, 100]} ticks={[0, 25, 50, 75, 100]} tick={{ fill: 'var(--muted)', fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={(value: number) => `${value}%`}/>
          <Tooltip formatter={(value, name) => [`${value ?? 0}%`, name === 'percentual' ? 'Concluído' : name]} contentStyle={{ background: 'var(--surface-raised)', color: 'var(--ink)', borderColor: 'var(--line)', borderRadius: '12px' }}/>
          <Bar dataKey="percentual" name="Concluído" fill="var(--purple)" maxBarSize={64} radius={[7, 7, 0, 0]} isAnimationActive={false}/>
        </BarChart>
      </ResponsiveContainer>
    </div>
  </section>;
}
