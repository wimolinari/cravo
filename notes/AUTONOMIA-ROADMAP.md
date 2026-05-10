# Roadmap — Autonomia do Claude em sessões longas

> **Status**: ideias para desenvolver depois. Não fazer agora.
>
> **Origem**: ao longo da sessão de implementação do chatbot do Cravo (maio 2026), ficou
> clara a fricção de aprovar manualmente cada permissão nova durante smoke tests/deploys
> longos. O Claude consegue trabalhar autonomamente em ediçoes (graças ao
> `defaultMode: "acceptEdits"`), mas comandos shell ainda interrompem o fluxo.

## Estado atual (10/05/2026)

### Já funciona automaticamente
- ✅ Edit/Write/Read sem aprovar (default `acceptEdits` no global)
- ✅ "Always allow" nos prompts grava o pattern em `settings.local.json` automaticamente
- ✅ Sessões futuras no mesmo projeto **não pedem de novo** (cache local)
- ✅ Patterns globais em `~/.claude/settings.json` aplicam a todos projetos

### Estatísticas atuais
- `~/.claude/settings.json` (global): **199 patterns** + 19 deny
- `Cravo/.claude/settings.local.json`: **106 patterns** (32 específicos do projeto)
- Outros projetos populados: Route_RedesSociais (379), Site Route Automotive (43), Projeto_Ofertas_TP (40)

### Fricções identificadas
1. **Cada smoke test introduce comandos novos** (echo `=== ... ===`, curl complexos, pipes diferentes) — Claude pede aprovação para cada um.
2. **Mesmo um pattern genérico tipo `Bash(curl * | python *)` exige confirmação** se variações pequenas mudam o "shape" do comando.
3. **Sessões longas perdem contexto** quando há fricção repetida (interrompe o fluxo de pensamento).
4. **Patterns excessivamente específicos da sessão** vão para o local sem real reuso futuro (ex.: `Bash(echo "=== Body do erro 500 ===" *)`)

## Ideias para evoluir (rascunho)

### 1. Configuração mais permissiva via terminal (fora do Claude Desktop)
> O usuário comentou que rodar Claude diretamente do terminal pode ser mais eficiente.

- **`claude` CLI** (oficial da Anthropic) já permite `--dangerously-skip-permissions` em sessões interativas
- Pode-se configurar via variáveis de ambiente:
  ```
  CLAUDE_PERMISSIONS_MODE=bypassPermissions
  ```
- Modo `plan` para aprovar plano upfront e depois deixar autoexecutar

### 2. Hooks de pré-processamento
- Hook `tool-use:request` que filtra/aprova automaticamente baseado em regras locais
- Ex.: qualquer `Bash(curl https://routepesquisa.com.br/*)` aprovado sem prompt, mesmo sem pattern explícito
- Permite regras compostas: "se tag é safe + projeto é Cravo → aprovar"

### 3. Modo "auto-pilot" temporário
- Comando `/autopilot 30min` que aprova tudo (exceto deny rules) por uma janela de tempo
- Útil para sessões intensivas de smoke test/deploy
- Volta ao modo normal automaticamente após o timeout

### 4. Limpeza/curadoria periódica do settings.local.json
- Hoje muitos patterns são "lixo" (echos específicos da sessão)
- Script `claude-settings-clean.py` que remove patterns que não foram usados em N dias
- Ou: agrupar patterns similares (`echo === * ===`, `echo "Inicio *"`) em um único genérico

### 5. Pre-aprovação por skill
- Quando uma skill é invocada (ex.: `krella-deploy-safe`), liberar automaticamente o conjunto de
  permissions que ela tipicamente usa, sem precisar listar cada uma.
- Skills declarariam suas dependências de tools no frontmatter.

### 6. Sandbox aceito por padrão
- Claude Code já tem sandbox em alguns casos (sem rede ou só leitura)
- Default: aceitar tudo sandboxed. Só pedir aprovação para "sair do sandbox".

### 7. CLI vs Desktop
> Pesquisar/avaliar:

- Claude Code CLI standalone tem mais flags de bypass que o Desktop
- Claude Code com integração nativa do terminal (PowerShell/zsh) pode ter telemetria
  diferente que reduz falsos prompts
- VS Code extension vs Desktop App: confirmar qual tem menos fricção

## Próximas decisões (quando voltar a esse tópico)

1. Avaliar se vale CLI puro vs Desktop App pra fluxos longos
2. Criar `claude-settings-merge.py` que junta patterns de N projetos no global, deduplica e remove pattern-junk
3. Definir critério: "se um pattern aparece em ≥3 projetos, promover para global automaticamente"
4. Investigar hooks da Anthropic (se já existem em alguma versão beta)
5. Considerar criar uma "skill de skills" — meta-skill que gerencia permissions cross-projeto

## Observações da sessão atual

Comandos que apareceram **muitas vezes** mas com pequenas variações (candidatos a
generalização):

- `curl -s -N --no-buffer -X POST <URL> --data @/tmp/X --max-time NN`
- `cat > /tmp/X.json << 'EOF' ... EOF`
- `echo "===" + comando + echo` (visual delimiters)
- `cmd //c "<exec>" 2>&1 | tail -N`
- Loops `for X in ...; do curl ... done`

Patterns globais já adicionados pra cobrir muitos desses (ver `~/.claude/settings.json`).

---

*Criado: 10/05/2026 · Última atualização: 10/05/2026*
