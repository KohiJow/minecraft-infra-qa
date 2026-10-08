# Arquitetura

```
                    ┌──────────────────────────────┐
   Discord  ───────▶│  bot de operação (Python)    │
                    │  59 comandos                 │
                    │  troca de mundo e instância  │
                    └───────────┬──────────────────┘
                                │ systemd + console
          ┌─────────────────────┴─────────────────────┐
          ▼                                           ▼
 ┌──────────────────┐   Conflicts=    ┌──────────────────────┐
 │ instância A      │◀───────────────▶│ instância B          │
 │ engine atual     │  exclusão mútua │ engine anterior      │
 │ 4 mundos         │                 │ 1 mundo (236 mods)   │
 └──────────────────┘                 └──────────────────────┘
          │        ambas na MESMA porta de jogo         │
          └─────────────────────┬─────────────────────-─┘
                                ▼
 ┌───────────────────────────────────────────────────────────┐
 │ servidor de downloads (HTTP, somente leitura, com Range)  │
 │  • pacotes de mods por mundo   • índice gerado            │
 │  • backups publicados          • página explicativa       │
 └───────────────────────────────────────────────────────────┘
                                ▲
                    ┌───────────┴───────────┐
                    │ rotina de backup      │
                    │ timer diário, 3/mundo │
                    └───────────────────────┘
```

## Decisões que valem explicar

**Mesma porta, exclusão mútua.** As duas instâncias usam engines de versões
diferentes e não podem rodar juntas, 4 núcleos e 22 GB não comportam. Usar a
mesma porta mantém o endereço estável para os jogadores. A garantia de que só
uma sobe é do systemd (`Conflicts=` nos dois sentidos), não do bot: assim vale
mesmo se alguém iniciar um serviço na mão.

**Soquete de console separado.** A segunda instância usa um soquete próprio de
multiplexador. Sem isso o processo nasce fora do cgroup da unidade e o systemd
recusa supervisioná-lo.

**Ajustes por mundo.** Dificuldade, PvP e pacote de recursos são globais no
arquivo de configuração do jogo. Um mapeamento por mundo é aplicado na troca,
senão o pacote de um mundo vaza para outro.

**Moldes.** Mundos de partida curta guardam uma cópia congelada do estado
inicial. Restaurar é trocar a pasta, segundos, não minutos.

**Pré-geração.** Geração de terreno sob demanda com muitos jogadores é o maior
risco de travamento (ver incidente 1). O mapa é gerado antes, em janela sem
ninguém online.
