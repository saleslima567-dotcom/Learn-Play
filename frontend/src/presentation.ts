// Shared presentation helpers for LearnPlay UI.
export const money = (n: number) => n === 0 ? 'Gratuito' : n.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
export const glyph = (c: string) => ({ violet: '</>', orange: '◈', blue: '⌘', green: '✳' } as Record<string, string>)[c] || '✦';

export const lessonCount = (count: number) => count === 1 ? '1 aula' : `${count} aulas`;
