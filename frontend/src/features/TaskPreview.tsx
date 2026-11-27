import { useState } from 'react';

export function TaskPreview() {
  const [tasks, setTasks] = useState([{ id: 0, label: 'Executar meu primeiro programa', done: false }]);
  const [input, setInput] = useState('');
  const completed = tasks.filter(task => task.done).length;

  return <section className="task-preview" aria-label="Prévia interativa da lista de tarefas">
    <small className="eyebrow">Prévia interativa · Python</small>
    <h2>Minha lista de tarefas</h2>
    <p>Experimente o resultado que você vai construir no terminal.</p>
    <form onSubmit={event => {
      event.preventDefault();
      const label = input.trim();
      if (!label || tasks.length >= 8) return;
      setTasks(items => [...items, { id: items.length, label, done: false }]);
      setInput('');
    }}>
      <label htmlFor="preview-task">Nova tarefa</label>
      <div><input id="preview-task" value={input} maxLength={80} disabled={tasks.length >= 8}
        onChange={event => setInput(event.target.value)} placeholder="Ex.: revisar variáveis" />
      <button className="primary" disabled={!input.trim() || tasks.length >= 8}>Adicionar</button></div>
    </form>
    <ul>{tasks.map(task => <li key={task.id}><label>
      <input type="checkbox" checked={task.done} onChange={() => setTasks(items =>
        items.map(item => item.id === task.id ? { ...item, done: !item.done } : item))} />
      <span>{task.label}</span>
    </label></li>)}</ul>
    <small role="status">{completed} de {tasks.length} concluídas{tasks.length >= 8 && ' · Limite de 8 tarefas nesta prévia'}</small>
  </section>;
}
