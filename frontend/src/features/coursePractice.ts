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

type PracticeSteps = Record<string, { mission: string; check: string; minutes: number }>;

const pythonSteps: PracticeSteps = {
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

const gitSteps: PracticeSteps = {
  'Versionamento na prática': {
    mission: 'Crie um repositório de treino no GitHub com um README. Clone-o, descreva o objetivo do projeto no arquivo e registre a alteração em um commit.',
    check: 'Execute git log -1 e confira sua mensagem. Com git status, verifique se todas as alterações foram registradas.',
    minutes: 10,
  },
  'Branches e merges': {
    mission: 'Crie a branch docs/como-usar com git switch -c docs/como-usar. Adicione uma seção de uso ao README e faça um commit nessa branch.',
    check: 'Compare a branch com a principal usando git diff main...HEAD. Se a sua branch principal tiver outro nome, use esse nome no comando.',
    minutes: 15,
  },
  'Pull requests': {
    mission: 'Envie a branch com git push -u origin docs/como-usar e abra um pull request para a branch principal do seu repositório de treino. Explique o que mudou, revise o diff e faça o merge.',
    check: 'O pull request aparece como integrado e a seção de uso está no README da branch principal. Guarde o link do seu pull request.',
    minutes: 15,
  },
};

export function practiceSteps(course: C): PracticeSteps {
  if (hasTaskProject(course)) return pythonSteps;
  if (course.category === 'Tecnologia' && course.title === 'Git e GitHub para equipes') return gitSteps;
  return {};
}

export function normalizeSearch(value: string) {
  return value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('pt-BR').trim();
}

export function lessonTime(minutes: number) {
  if (minutes < 60) return `${minutes} min`;
  const rest = minutes % 60;
  return `${Math.floor(minutes / 60)} h${rest ? ` ${rest} min` : ''}`;
}
