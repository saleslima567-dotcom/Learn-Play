import type { C } from '../model';

export const levelGuides: Record<string, string> = {
  Iniciante: 'Comece pelos fundamentos, mesmo no seu primeiro contato com o assunto.',
  Intermediário: 'Indicado para quem já conhece os fundamentos e quer aplicá-los.',
  Avançado: 'Indicado para quem já pratica o assunto com autonomia.',
  'Todos os níveis': 'Percurso aberto a alunos com diferentes níveis de experiência.',
};

export const categoryGoals: Record<string, string> = {
  Programação: 'Aprender a programar',
  Design: 'Desenhar interfaces',
  Tecnologia: 'Usar ferramentas de tecnologia',
  Negócios: 'Desenvolver habilidades de negócio',
};

export const pythonSteps: Record<string, { mission: string; check: string; minutes: number }> = {
  'Primeiros passos com Python': {
    mission: 'Crie tarefas.py e use print() para exibir o nome da sua lista.',
    check: 'Ao executar o arquivo, o título aparece no terminal.', minutes: 5,
  },
  'Variáveis e tipos de dados': {
    mission: 'Guarde duas tarefas em uma lista de strings e exiba cada item pelo índice.',
    check: 'Você consegue trocar um item sem alterar o outro.', minutes: 10,
  },
  'Decisões e repetições': {
    mission: 'Use um laço para listar as tarefas. Se a lista estiver vazia, mostre uma mensagem.',
    check: 'Execute o programa com duas tarefas e depois com uma lista vazia.', minutes: 10,
  },
  'Projeto: lista de tarefas': {
    mission: 'Crie um menu para adicionar tarefas, marcar uma como feita, listar os itens e sair.',
    check: 'Adicione duas tarefas, conclua apenas a primeira e confira o estado de ambas.', minutes: 20,
  },
};

export function hasTaskProject(course: C) {
  const topics = course.lesson_titles ?? course.lessons?.map(lesson => lesson.title) ?? [];
  return course.category === 'Programação' && /\bpython\b/i.test(course.title)
    && topics.includes('Projeto: lista de tarefas');
}

export function normalizeSearch(value: string) {
  return value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('pt-BR').trim();
}

export function lessonTime(minutes: number) {
  if (minutes < 60) return `${minutes} min`;
  const rest = minutes % 60;
  return `${Math.floor(minutes / 60)} h${rest ? ` ${rest} min` : ''}`;
}
