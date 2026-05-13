# PLAN.md — Tarefas do agente

> Edite este arquivo para listar o que o agente deve fazer na próxima sessão.
> Use checkboxes `[ ]` / `[x]`. O agente vai marcar conforme concluir.

- [x] Analisar os links de videos do youtube. 1) São videos ativos, ou seja, são gravações de um humano tocando, ou somente imagem estática com musica tocando. Se for somente imagem estática, alertar no arquivo .xlsx
- [x] Gerar arquivo VideosYoutude.xlsx no diretório com todos Origem|Link|Status do link|

> **Sessão 0dcc3eea (2026-05-12):**
> - `VideosYoutude.xlsx` gerado na raiz: 260 linhas (Origem | Link | Status).
>   Todos os 49 vídeos únicos estão classificados como HUMAN_LIKELY (232 linhas)
>   ou PROBABLY_HUMAN (28). **ZERO vídeos estáticos** restantes — a auditoria
>   da sessão anterior (2fb8e441) removeu todos os 49 audio-only.
> - `revisao_atualizado.xlsx` também gerado com 2 sheets (Links Externos +
>   Videos YouTube). Não foi salvo como `revisao.xlsx` porque o arquivo estava
>   aberto no Excel do Wilson (PID 11340). Para promover: fechar Excel +
>   `mv revisao_atualizado.xlsx revisao.xlsx`.
