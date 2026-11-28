import type { C } from '../model';

type PythonLesson = {
  explanation: string[];
  example: string;
  expected: string;
  exercise: string;
  check: string;
};

const pythonLessons = new Map<string, PythonLesson>([
  ['Primeiros passos com Python', {
    explanation: [
      'Um programa em Python é um arquivo de texto com instruções. Salve o primeiro exemplo como tarefas.py e abra o terminal na pasta do arquivo. Execute python tarefas.py, ou python3 tarefas.py se esse for o comando disponível no seu ambiente.',
      'A função print() escreve uma mensagem no terminal. As aspas indicam que o conteúdo é texto. Python executa as instruções deste exemplo de cima para baixo.',
    ],
    example: `# Mostra o título da lista.
print("Minhas tarefas")

# Cada chamada de print() começa uma nova linha.
print("1. Revisar a aula")
print("2. Fazer o exercício")`,
    expected: 'O terminal mostra o título e as duas tarefas, cada texto em uma linha.',
    exercise: 'Troque o título e adicione uma terceira tarefa usando print(). Salve o arquivo e execute de novo.',
    check: 'Confira se o novo título aparece primeiro e se sua terceira tarefa aparece na última linha.',
  }],
  ['Variáveis e tipos de dados', {
    explanation: [
      'Uma variável dá um nome a um valor. Aqui, titulo é um texto (str) e tarefas é uma lista de textos. len(tarefas) devolve um número inteiro (int), com a quantidade de itens.',
      'A primeira posição de uma lista é 0. A segunda é 1. Você pode alterar uma posição sem recriar a lista toda.',
    ],
    example: `titulo = "Minhas tarefas"
tarefas = ["Revisar a aula", "Fazer o exercício"]

# A posição 1 é a segunda tarefa.
tarefas[1] = "Testar o programa"

print(titulo)
print(tarefas[0])
print(tarefas[1])
print(len(tarefas))  # Mostra a quantidade de itens.`,
    expected: 'A primeira tarefa continua sendo Revisar a aula. A segunda vira Testar o programa. A quantidade continua sendo 2.',
    exercise: 'Crie uma lista com três tarefas. Altere apenas a última e use print() para verificar as três posições.',
    check: 'Confira se as duas primeiras continuam iguais e se len(tarefas) retorna 3.',
  }],
  ['Decisões e repetições', {
    explanation: [
      'Use if para decidir o que fazer. A expressão not tarefas é verdadeira quando a lista está vazia. O bloco else é executado quando há itens.',
      'Um laço for percorre a lista, um item de cada vez. O recuo das linhas indica quais instruções pertencem ao if, ao else ou ao laço.',
    ],
    example: `tarefas = ["Revisar a aula", "Testar o programa"]

if not tarefas:
    print("Nenhuma tarefa por enquanto.")
else:
    # A variável tarefa recebe um item por vez.
    for tarefa in tarefas:
        print("-", tarefa)`,
    expected: 'Com dois itens, o terminal mostra as duas tarefas. Com tarefas = [], aparece apenas a mensagem de lista vazia.',
    exercise: 'Execute com a lista vazia e com três tarefas. Depois, altere o texto exibido no caso vazio.',
    check: 'A mensagem só aparece quando não há tarefas. Com três tarefas, o programa exibe três linhas.',
  }],
  ['Projeto: lista de tarefas', {
    explanation: [
      'O menu repete enquanto o programa está aberto. Cada tarefa é um dicionário com um texto e um estado. Quando o aluno marca uma tarefa, seu estado muda de False para True.',
      'O menu numera os itens a partir de 1 para facilitar a leitura. Ao escolher um item, subtraia 1 para encontrar a posição na lista.',
    ],
    example: `tarefas = []

while True:
    opcao = input("1 Adicionar | 2 Listar | 3 Concluir | 0 Sair: ")

    if opcao == "1":
        texto = input("Nova tarefa: ").strip()
        if texto:
            tarefas.append({"texto": texto, "concluida": False})
    elif opcao == "2":
        if not tarefas:
            print("Nenhuma tarefa por enquanto.")
        for numero, tarefa in enumerate(tarefas, start=1):
            estado = "feita" if tarefa["concluida"] else "pendente"
            print(numero, tarefa["texto"], "-", estado)
    elif opcao == "3":
        numero = input("Número da tarefa: ").strip()
        if numero.isascii() and numero.isdecimal() and 1 <= int(numero) <= len(tarefas):
            # O número exibido começa em 1, o índice começa em 0.
            tarefas[int(numero) - 1]["concluida"] = True
        else:
            print("Escolha um número da lista.")
    elif opcao == "0":
        break
    else:
        print("Opção inválida.")`,
    expected: 'Você consegue adicionar, listar e concluir tarefas enquanto o menu está aberto. Os itens ficam em memória durante esta execução.',
    exercise: 'Adicione duas tarefas, conclua a primeira e liste de novo. Tente concluir um número que não existe antes de sair.',
    check: 'A primeira fica feita, a segunda continua pendente e um número inválido recebe uma mensagem sem interromper o programa.',
  }],
]);

export function hasWrittenPythonCourse(course: C) {
  return course.instructor_is_demo === true && course.title === 'Python do zero ao primeiro projeto';
}

export function pythonLessonFor(course: C, title: string) {
  return hasWrittenPythonCourse(course) ? pythonLessons.get(title) : undefined;
}
