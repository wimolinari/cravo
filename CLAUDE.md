# CLAUDE.md — Projeto Cravo

Instruções permanentes pra qualquer instância do Claude Code que abrir neste
projeto, seja autônoma (via Claude Orchestrator) ou interativa (CLI / desktop).

## Bootstrap obrigatório — leia ANTES de qualquer ação

Toda sessão do Claude Code neste projeto deve, antes de fazer qualquer mudança
ou responder ao usuário sobre o estado atual do trabalho, ler na seguinte ordem:

1. `.agent/HISTORY.md` — narrativa de todas as sessões autônomas anteriores.
   Tarefas concluídas, arquivos tocados, validações executadas, próximos passos
   sugeridos. Esse é o melhor resumo de "onde paramos da última vez".
2. `.agent/BLOCKERS.md` — se NÃO estiver vazio, há decisão humana pendente que
   pode invalidar o trabalho atual. Trate primeiro ou ao menos confirme com o
   usuário se ainda se aplica.
3. `.agent/PLAN.md` — backlog atual: itens `- [ ]` são pendentes, `- [x]` são
   concluídos pelas sessões autônomas.
4. `.agent/STATUS.json` — último estado conhecido (commit que ficou de pé,
   timestamps, etc.).

**Se você estiver no modo desktop/CLI interativo:** depois de ler, imprima um
recap curto pro usuário (qual o último trabalho, o que pendente, se tem
bloqueio) antes de aceitar a próxima instrução. Isso evita que o usuário e
você comecem do zero quando na verdade já temos contexto sólido em `.agent/`.

**Se você estiver no modo autônomo (orquestrador):** o protocolo injetado no
prompt inicial já cobre o bootstrap, mas as regras acima continuam válidas como
fonte da verdade.

## Contexto
Projeto localizado em `C:\Outros\Cravo`. Este arquivo foi gerado automaticamente
pelo Claude Orchestrator porque não havia `CLAUDE.md` quando o projeto foi
cadastrado.

Edite livremente para documentar:
- Stack e ferramentas.
- Convenções de código.
- Comandos úteis (build, testes, lint).
- Decisões arquiteturais relevantes.
- O que NÃO mexer.

## Coordenação com o orquestrador
A pasta `.agent/` é o canal entre o agente (qualquer Claude Code) e o orquestrador.
Quando disparado em modo autônomo, siga o protocolo injetado no prompt inicial:
atualize `.agent/STATUS.json`, `.agent/HEARTBEAT.txt`, marque tarefas no
`.agent/PLAN.md` e pare em `.agent/BLOCKERS.md` se precisar de decisão humana.
