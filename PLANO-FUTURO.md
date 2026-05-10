# Plano de evolução — Tratados do Cravo

> **Status atual (2026-05-10):** site visual completo publicado em
> https://routepesquisa.com.br/cravo/ com 27 partituras navegáveis no visualizador, 60+
> exemplos inline nas páginas dos tratados, dicionário interativo de 70 termos, lightbox com
> zoom, video-pickers para gravações canônicas, e PDF original disponível para download.

---

## Visão de produto

A plataforma evolui de **edição interativa de UM tratado** para **gerador de conteúdo
pedagógico-musical a partir de PDFs**. O Cravo é o protótipo; o destino é uma plataforma
genérica capaz de transformar tratados, métodos e manuais (música ou outras áreas — médica,
jurídica, técnica) em sites navegáveis, com chatbot de apoio e síntese audiovisual de exemplos.

**Princípios:**
- O PDF original é a *fonte canônica*; tudo o que se gera é derivado e auditável de volta a ele.
- O conhecimento é organizado em três camadas: **texto traduzido + glossário** → **navegação
  por temas e cruzamentos** → **mídia gerada** (áudio, vídeo, animações).
- Direitos autorais dos tradutores são preservados em todas as camadas.

---

## Feature 1 — Chatbot pedagógico (Claude API)

### Objetivo
Estudante pergunta sobre técnica/teoria/repertório do cravo barroco; o chatbot responde com:
1. Texto explicativo no estilo do site (não inventado, citando tratados).
2. Trecho citado do tratado (com link âncora exato).
3. Imagem relevante (partitura, tabela de ornamentos, gravura).
4. Vídeo de gravação canônica quando aplicável.

### Arquitetura

```
┌──────────────────────────────────────────────────────────────┐
│ FRONTEND (estático, mesmo padrão do site atual)              │
│  ─────────────────────────────────────────────────────────   │
│  • assets/chatbot.js — UI flutuante (canto inferior direito) │
│  • Histórico em localStorage (privacidade-first)             │
│  • Markdown rendering com citation popups                    │
└──────────────────────────────────────────────────────────────┘
                          │
                          ▼ POST /api/chat
┌──────────────────────────────────────────────────────────────┐
│ BACKEND minimal — Python/FastAPI ou Node                     │
│  ─────────────────────────────────────────────────────────   │
│  • /api/chat → recebe {question, history}                    │
│  • Retorna {answer_md, citations[], related_images[],         │
│            related_videos[]}                                  │
│  • Lê chave do .env (ANTHROPIC_API_KEY)                       │
└──────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────────┐
│ Claude API (Sonnet 4.5/Haiku) com prompt engineering         │
│  ─────────────────────────────────────────────────────────   │
│  System prompt inclui:                                        │
│  • Texto integral dos 4 tratados (em /pages/page-NNN.txt)     │
│  • Glossário (70 termos, JSON)                                │
│  • Inventário de imagens (paths + captions)                   │
│  • Mapping URL→tópicos (sancta-maria.html#cap18 = dedilhado)  │
│  Instructions: "responder citando o tratado por capítulo,     │
│  com âncora ao site, e indicando até 3 imagens/vídeos         │
│  relacionados do inventário fornecido."                       │
└──────────────────────────────────────────────────────────────┘
```

### Implementação técnica

**1. Knowledge base** (já temos):
- 122 páginas extraídas em `/pages/page-NNN.txt`
- 167 imagens de partituras catalogadas em `/site/partituras/index.json`
- 70 termos do glossário em `/site/assets/glossario.js`
- URLs canônicas mapeadas no plano de site

**2. Prompt caching** (essencial para custo):
- Cabeçalho fixo com tratados+glossário+inventário → ~50K tokens cacheable
- TTL 5min, hit rate 90%+ esperado em sessões com >2 perguntas
- Custo estimado: ~$0.001/pergunta (Haiku 4.5) ou $0.01/pergunta (Sonnet)

**3. Tool use (opcional)**:
- `lookup_term(key)` — busca no glossário
- `find_score(query)` — busca semântica nas captions de imagens
- `find_video(piece_name)` — retorna IDs de YouTube curados

**4. Streaming** com SSE para UX (resposta aparecendo conforme gerada).

### UI/UX

```html
<!-- Canto inferior direito -->
<button class="chatbot-fab">💬 Perguntar ao Tratado</button>

<!-- Painel expandido -->
<div class="chatbot-panel">
  <header>Chat com os tratados</header>
  <div class="messages">
    <div class="msg user">Como Couperin sugere começar um trinado?</div>
    <div class="msg assistant">
      Couperin descreve três fases para o trinado:
      <ol>
        <li>Apoio sobre a nota acima da principal</li>
        <li>Batimentos</li>
        <li>Ponto de parada</li>
      </ol>
      <cite>↗ <a href="tratados/couperin.html#ornamentos">Couperin · Ornamentos</a></cite>

      <figure class="related-score">
        <img src="partituras/couperin/embedded/p107-img1.jpeg">
        <figcaption>Tabela de Ornamentos · 1713</figcaption>
      </figure>

      <div class="related-video">
        <a href="...">▶ Skip Sempé · Sarabande de Rameau (trinados em prática)</a>
      </div>
    </div>
  </div>
  <form><input placeholder="Sua pergunta..."></form>
</div>
```

### Esforço estimado
- Backend FastAPI minimal + Anthropic SDK: **1 dia**
- Frontend chatbot UI: **1 dia**
- Prompt engineering + ajuste fino: **1 dia**
- Testes pedagógicos com perguntas reais: **1 dia**
- **Total: 4 dias** para MVP.

### Hospedagem
- Backend: Railway / Fly.io / Render (free tier suficiente para uso pessoal)
- Frontend: já no IIS atual, só precisa apontar fetch para API URL

---

## Feature 2 — Partitura → MIDI/MP3 + Vídeo com teclado virtual

### Objetivo
A partir de uma imagem de partitura selecionada no `partituras-viewer.html`, gerar:
1. **Arquivo `.mid`** (MIDI) — para download e abertura em DAW/MuseScore.
2. **Arquivo `.mp3`** (síntese de cravo) — para escuta direta.
3. **Vídeo `.mp4`** com teclado virtual mostrando teclas pressionadas sincronizadas com a
   notação destacando o compasso atual — estilo MuseScore Player ou Synthesia.

### Pipeline

```
┌──────────────────────────────────────────────────────────────┐
│ FASE 1 — OMR (Optical Music Recognition)                     │
│  ─────────────────────────────────────────────────────────   │
│  Imagem da partitura  →  Audiveris (open-source) ou           │
│                          Oemer (deep learning)                │
│  Saída: MusicXML (formato padrão de notação)                  │
└──────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────────┐
│ FASE 2 — Curadoria humana (CRÍTICA)                          │
│  ─────────────────────────────────────────────────────────   │
│  OMR de partituras barrocas é IMPRECISA em ~30% das notas.   │
│  Solução: editor MusicXML inline (ex.: OpenSheetMusicDisplay  │
│  + editor manual) onde o usuário corrige antes de exportar.   │
│  Alternativa: gerar MusicXML uma vez por partitura, salvar    │
│  em /partituras/musicxml/ e reutilizar.                       │
└──────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────────┐
│ FASE 3 — Síntese                                             │
│  ─────────────────────────────────────────────────────────   │
│  MusicXML → MIDI: música21 (Python) ou Verovio (JS)          │
│  MIDI → MP3:  FluidSynth + soundfont de cravo                │
│  Soundfonts recomendados:                                    │
│    • Sonatina Symphonic Orchestra (CC0) → cravo               │
│    • Salamander GrandPiano (CC-BY) — pra fallback             │
│    • Idealmente: amostras de cravo histórico (ex.: Ruckers)   │
└──────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────────┐
│ FASE 4 — Vídeo sincronizado                                  │
│  ─────────────────────────────────────────────────────────   │
│  Opção A: BROWSER-SIDE (sem backend)                          │
│    • OpenSheetMusicDisplay para renderizar partitura          │
│    • Tone.js + soundfont-player para tocar MIDI               │
│    • Web Audio + Canvas para teclado virtual animado          │
│    • Mediarecorder API para gravar vídeo .webm                │
│                                                               │
│  Opção B: SERVER-SIDE (mais robusto)                          │
│    • FFmpeg com filter_complex                                │
│    • Frame por frame: imagem partitura + retângulo destacando │
│      compasso + teclado SVG com teclas vermelhas              │
│    • Áudio: MIDI sintetizado em mp3                           │
└──────────────────────────────────────────────────────────────┘
```

### MVP simplificado (sem OMR)

Como OMR de partituras barrocas com dedilhado anotado é difícil, o MVP pode pular OMR:

1. **Curadoria manual em MusicXML** — para cada uma das 27 partituras do viewer, criar
   manualmente o MusicXML correspondente (uma vez só). 1-2h por partitura simples.
2. **Player web 100% browser-side** usando OpenSheetMusicDisplay + Tone.js:
   - Renderiza a partitura novamente (não usa o JPEG)
   - Toca via Web Audio com soundfont de cravo
   - Highlight de compasso atual sincronizado
   - Botão "▶ Tocar"

3. **Teclado virtual** abaixo da partitura: 5 oitavas, teclas pressionadas em vermelho
   conforme nota toca (mesma técnica do site Synthesia).

### Tecnologias

| Componente | Lib / serviço | Licença |
|---|---|---|
| OMR | [Oemer](https://github.com/BreezeWhite/oemer) | AGPL-3.0 |
| Renderização | [OpenSheetMusicDisplay](https://github.com/opensheetmusicdisplay/opensheetmusicdisplay) | BSD-3 |
| Síntese áudio | [Tone.js](https://tonejs.github.io/) | MIT |
| Soundfont | [smplr](https://github.com/danigb/smplr) com cravo | MIT |
| MIDI export | [music21](http://web.mit.edu/music21/) ou [tonejs-midi](https://github.com/Tonejs/Midi) | BSD/MIT |
| Vídeo encoding | FFmpeg WASM | LGPL-2.1 |

### Esforço estimado
- **MVP (3 partituras curadas, player browser-side):** 1 semana
  - Dia 1-2: curadoria manual MusicXML para Alemanda + Prelúdio 1 + Primeira Lição de Rameau
  - Dia 3: integração OpenSheetMusicDisplay + Tone.js no `partituras-viewer.html`
  - Dia 4: teclado virtual SVG sincronizado
  - Dia 5: gravação de vídeo via MediaRecorder + download .webm
- **Fase 2 (OMR + 27 partituras):** 2-3 semanas
- **Fase 3 (vídeo server-side ffmpeg em alta qualidade):** +1 semana

### UX no `partituras-viewer.html`

```
┌────────────────────────────────────────────────────────────┐
│ Selecione obra: [Alemanda                              ▼]  │
│ [▶ Tocar] [⏸ Pause] [⏹ Stop] [⬇ MIDI] [⬇ MP3] [🎬 Vídeo]   │
├────────────────────────────────────────────────────────────┤
│                                                            │
│   [partitura renderizada com compasso atual destacado]    │
│                                                            │
│                                                            │
│ ┌─────────────────────────────────────────────────────────┐│
│ │     Teclado virtual (5 oitavas)                         ││
│ │ ▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌ ││
│ │ │█│█│█│█│█│█│█│█│█│█│█│█│█│█│█│█│█│█│█│█│█│█│█│█│█│█│ ││
│ └─────────────────────────────────────────────────────────┘│
│                                                            │
│ Tempo: ♩=72  · Volume: ▮▮▮▮▯  · Loop: ☐                   │
└────────────────────────────────────────────────────────────┘
```

---

## Roadmap de produto

### M0 — Atual (concluído)
- ✅ Site visual completo
- ✅ 27 partituras navegáveis
- ✅ Glossário interativo
- ✅ Vídeos curados
- ✅ Apresentação/Prefácio/Notas Críticas integrais
- ✅ PDF original disponível

### M1 — Chatbot pedagógico (4 dias)
- Backend FastAPI + Anthropic SDK
- Frontend bubble + painel
- Prompt engineering com tratado integral
- Citation popups + imagens relacionadas

### M2 — Player MIDI/Áudio (1 semana)
- 3 partituras curadas em MusicXML
- OpenSheetMusicDisplay + Tone.js
- Teclado virtual sincronizado
- Download .mid e .mp3

### M3 — Vídeo + 27 partituras (2-3 semanas)
- Curadoria MusicXML para todas as 27
- Integração OMR para futuras partituras
- Gravação .webm/.mp4 via MediaRecorder

### M4 — Plataforma genérica (futuro)
- Pipeline de ingestão: PDF → texto extraído → glossário sugerido por LLM →
  imagens classificadas → site gerado automaticamente
- Templates por área: música clássica, medicina, direito, técnica
- Marketplace de tratados convertidos
- White-label para universidades

---

## Considerações de custo (mensal, uso moderado)

| Item | Plataforma | Custo estimado |
|---|---|---|
| Hospedagem frontend | IIS atual / Cloudflare Pages | $0 |
| Backend chatbot | Railway hobby tier | $5 |
| Claude API (1000 perguntas/mês com cache) | Anthropic | $20-50 |
| Storage de áudio/vídeo | Backblaze B2 / Cloudflare R2 | $1 |
| **Total** | | **$26-56/mês** |

Para piloto com 1 universidade pode rodar de graça em Cloudflare Workers + Pages.

---

## Próximos passos sugeridos

1. **Validar feature 1 (chatbot) com perguntas reais** — listar 20 perguntas de estudantes de
   cravo iniciantes/avançados e ver quais o site atual já responde via navegação. As que
   *não* respondem são o caso de uso primário do chatbot.

2. **Curar 3 partituras em MusicXML** como teste piloto — Primeira Lição de Rameau é a mais
   simples (apenas 8 notas em escala). Excelente starter.

3. **Decisão de arquitetura**: tudo browser-side (mais simples, sem custos) ou backend
   (mais robusto, mais flexível, custo de hospedagem).

4. **Aprovação do escopo M1** antes de começar.

---

*Este plano foi gerado a partir do trabalho de inventário e organização realizado no projeto
Cravo (5 dias de trabalho · 27 partituras · 122 páginas auditadas). É um documento vivo —
atualize conforme o produto evolui.*
