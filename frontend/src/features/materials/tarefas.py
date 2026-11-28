tarefas = []

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
        print("Opção inválida.")
