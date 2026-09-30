# Bola de voz e interação com o mouse

## Implementação

A bola existente permanece no elemento `#orb-stage` de
`src/renderer/index.html`. A forma visual é o `.orb-core`, com as partículas
já existentes em `.orb-particles`.

Nesta alteração foram modificados somente:

- `src/renderer/style.css`: transparência, vidro, neon contido, deformação e partículas;
- `src/renderer/renderer.ts`: leitura leve da posição do ponteiro para orientar a reação da bola;
- este documento.

O componente de estados em `src/renderer/components/orb.ts` não foi alterado.
Os estados existentes continuam sendo apenas visuais.

## Comportamento

- Parada: preenchimento translúcido, borda discreta e brilho azul mínimo.
- Entrada/permanência do mouse: `:hover` aumenta suavemente a borda, a luz e a saturação azul.
- Movimento: `pointermove` calcula a posição relativa do cursor em dois valores entre `-1` e `1`, aplicados às propriedades CSS `--pointer-x` e `--pointer-y`.
- Saída: `pointerleave` devolve esses valores para zero; as transições CSS fazem o retorno gradual.
- A forma usa `border-radius` assimétrico e `droplet-morph` para uma deformação orgânica pequena.
- As partículas existentes são poucas, ficam pausadas e transparentes fora do hover, e aparecem gradualmente próximas da bola.

O cálculo do ponteiro é limitado a um `requestAnimationFrame` por ciclo de pintura.
Não há loop contínuo novo, captura de áudio ou simulação física.

## Empacotamento

O aplicativo continua sendo Electron + TypeScript com electron-builder:

```powershell
pnpm run typecheck
pnpm run build
pnpm run dist
```

O instalador final fica em `release/AUTOWORK Setup 0.1.0.exe`. A configuração
NSIS existente cria o atalho `AUTOWORK` no Desktop e no Menu Iniciar. O pacote
unpacked fica em `release/win-unpacked/`.

## Execução

```powershell
pnpm start
```

Para testar o pacote instalado, execute o atalho `AUTOWORK` criado pelo
instalador. O backend Python e a integração de voz não foram modificados.

## Reversão

Este workspace não contém um repositório Git, portanto não há commit de
reversão disponível. Em um checkout Git, reverta os arquivos desta alteração:

```powershell
git restore src/renderer/style.css src/renderer/renderer.ts docs/voice-orb-interaction.md
```

Antes da alteração, os hashes dos arquivos visuais principais foram registrados
no relatório da tarefa.
