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

const designSteps: PracticeSteps = {
  'Princípios de UX': {
    mission: 'Desenhe um formulário de inscrição para uma oficina. Inclua nome, e-mail e um botão de envio. Peça a alguém que aponte por onde começaria e o que espera que aconteça ao enviar.',
    check: 'Anote uma dúvida observada no teste, ajuste o esboço e confira se a pessoa consegue explicar o próximo passo.',
    minutes: 15,
  },
  'Tipografia e cor': {
    mission: 'Refine o esboço: dê destaque ao título, mantenha um rótulo visível acima de cada campo e escreva uma instrução curta para o e-mail. Defina como distinguir um erro mesmo sem enxergar sua cor.',
    check: 'Veja o formulário em escala de cinza. O rótulo continua legível e a mensagem explica como corrigir o e-mail.',
    minutes: 15,
  },
  'Componentes e estados': {
    mission: 'Monte três telas do formulário: pronto para preencher, e-mail inválido e inscrição confirmada. Preserve o nome digitado na tela de erro e mostre o que acontece depois da confirmação.',
    check: 'Peça a alguém que simule o envio com e-mail inválido, corrija o campo e identifique a confirmação usando apenas suas telas.',
    minutes: 20,
  },
};

const communicationSteps: PracticeSteps = {
  'Comunicação clara': {
    mission: 'Imagine que uma equipe precisa adiar a entrega de sexta para segunda. Escreva um aviso de até quatro frases com a mudança, o motivo e o que cada pessoa precisa fazer agora.',
    check: 'Peça a um colega que leia o aviso e diga o novo prazo e a próxima ação. Revise o trecho que gerou dúvida.',
    minutes: 10,
  },
  'Feedback que desenvolve': {
    mission: 'No mesmo cenário, uma revisão chegou depois do combinado. Escreva um feedback privado que descreva o ocorrido, explique o impacto na equipe e abra espaço para ouvir a outra pessoa.',
    check: 'Sublinhe o fato observável, o impacto e a pergunta final. Reescreva qualquer frase que atribua uma intenção sem evidência.',
    minutes: 15,
  },
  'Plano de ação': {
    mission: 'Transforme o feedback em um plano de duas ações para a próxima entrega. Para cada ação, registre um responsável, uma data e uma evidência de conclusão.',
    check: 'Leia o plano como se fosse outra pessoa da equipe. Você consegue apontar quem fará o quê, até quando e como confirmar que foi feito?',
    minutes: 15,
  },
};

type CourseGuide = { steps: PracticeSteps; preparation: string };

const pythonGuide: CourseGuide = {
  steps: pythonSteps,
  preparation: 'Você pode começar do zero. Separe um editor de texto e um ambiente com Python 3, local ou online, em que possa criar e executar o arquivo tarefas.py.',
};

const courseGuides = new Map<string, CourseGuide>([
  ['Tecnologia/Git e GitHub para equipes', {
    steps: gitSteps,
    preparation: 'Tenha o Git instalado e uma conta no GitHub com permissão para criar um repositório de treino. Confira a instalação com git --version e saiba abrir o terminal na pasta do projeto.',
  }],
  ['Design/Design de interfaces digitais', {
    steps: designSteps,
    preparation: 'Você vai usar campos de texto, rótulos e botões. Separe papel e caneta ou um editor de protótipos e combine um teste curto com alguém que possa experimentar o formulário.',
  }],
  ['Negócios/Comunicação e liderança', {
    steps: communicationSteps,
    preparation: 'Você pode usar o cenário fictício das aulas. Separe um editor de texto ou caderno e convide alguém para ler seu aviso e dizer o que entendeu.',
  }],
]);

export function courseGuide(course: C) {
  if (hasTaskProject(course)) return pythonGuide;
  return courseGuides.get(`${course.category}/${course.title}`);
}

export function normalizeSearch(value: string) {
  return value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('pt-BR').trim();
}

export function lessonTime(minutes: number) {
  if (minutes < 60) return `${minutes} min`;
  const rest = minutes % 60;
  return `${Math.floor(minutes / 60)} h${rest ? ` ${rest} min` : ''}`;
}
