# Tratados do Cravo

Site digital interativo dos **4 tratados históricos sobre o cravo** apresentados na edição UFRJ 2013, com chatbot pedagógico baseado em Claude.

> **Site público:** https://routepesquisa.com.br/cravo/

## Os 4 tratados cobertos

| Ano  | Autor                        | Obra                                            |
|------|------------------------------|-------------------------------------------------|
| 1565 | Thomas de Sancta Maria       | *Livro chamado Arte de tocar Fantasia*          |
| 1637 | Girolamo Frescobaldi         | *Ao Leitor* (prefácio das Tocatas, Livro 1)     |
| 1717 | François Couperin            | *L'Art de toucher le Clavecin*                  |
| 1724 | Jean-Philippe Rameau         | *De la Mécanique des doigts sur le Clavessin*   |

## Estrutura

```
cravo/
├─ 2020tratadocravo.pdf        # PDF original (UFRJ 2013, 122 páginas)
├─ site/                        # Site estático (HTML/CSS/JS, sem framework)
│  ├─ index.html
│  ├─ tratados/                 # 1 página por tratado
│  ├─ temas/                    # 6 páginas temáticas (postura, dedilhado, etc.)
│  ├─ partituras/               # 28 partituras curadas + 114 imagens embedded
│  ├─ comparador.html           # Comparador lado a lado dos 4 autores
│  ├─ partituras-viewer.html    # Visualizador com zoom (fonte da curadoria)
│  ├─ glossario.html            # Dicionário (69 termos)
│  └─ assets/                   # CSS + JS compartilhados (style, lightbox, chatbot, ...)
├─ chatbot/                     # Chatbot pedagógico (Claude API)
│  ├─ build-knowledge.py        # Extrai PDF + glossário + curadoria
│  ├─ inject-chatbot.py         # Injeta CSS/JS em todos HTMLs do site
│  ├─ knowledge/                # Saída: tratado_full.txt, glossary.json, etc.
│  ├─ backend/                  # FastAPI + Anthropic SDK + prompt caching
│  └─ README.md                 # Como rodar/deployar o backend
├─ _deploy.bat                  # Deploy via robocopy para o servidor de produção
└─ PLANO-FUTURO.md              # Roadmap (M0→M4)
```

## Recursos do site (18 páginas)

- 4 páginas de tratado (uma por autor)
- 6 páginas temáticas (postura, dedilhados, ornamentos, articulação, ritmo-tempo, exercícios-baterias)
- Comparador 4×N (sinapse rápida entre tradições)
- Visualizador de partituras com 28 obras curadas
- Roteiro de estudo em 6 etapas
- Glossário interativo (69 termos com tooltips)
- PDF original navegável
- Apresentação + prefácio + créditos UFRJ
- Chatbot **Mestre do Cravo** integrado em todas as páginas

## Chatbot

Assistente pedagógico **Claude (Anthropic)** com prompt caching. Knowledge base:

- Texto integral dos 4 tratados (170 KB ≈ 50K tokens)
- Glossário do site (69 termos)
- Sitemap (17 URLs canônicas)
- 28 partituras curadas com título + descrição + nível
- 10 tópicos sugeridos como cards iniciais

UI: botão flutuante ✦ inferior direito → painel redimensionável (normal/expand/fullscreen)
+ múltiplas conversas em `localStorage` + export PDF.

Ver `chatbot/README.md` para custos estimados, deploy e troubleshooting.

## Como rodar localmente

```bash
# 1. Site estático
cd C:/Outros/Cravo/site
python -m http.server 8181
# → http://localhost:8181/

# 2. Chatbot backend (em outra janela)
cd C:/Outros/Cravo/chatbot/backend
run-backend.bat
# → http://127.0.0.1:8000/api/health
```

Pré-requisito: copiar `.env.example` → `.env` e preencher `ANTHROPIC_API_KEY`.

## Deploy em produção

```bat
:: Site estático (Windows share)
C:\Outros\Cravo\_deploy.bat
```

Atualmente publicado em `\\10.10.100.10\d$\Websites\routepesquisa.com.br\cravo` →
`https://routepesquisa.com.br/cravo/`.

## Créditos

Edição UFRJ 2013 — *Tratados e Métodos de Teclado: Fontes para o estudo do cravo nos séculos XVI a XVIII*.

Site digital e chatbot construídos como camada de leitura interativa sobre o material original.
