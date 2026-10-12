# Créditos e autoria

O **Pseudonimizador** foi desenvolvido e é mantido pelo **Juiz do Trabalho
Maurício Schmidt Bastos (TRT4)**.

## Origem do motor

O motor de pseudonimização (`pseudonimizador/motor/`) é cópia do pacote
`ulpiano/nucleo/privacidade/` do **Ulpiano**, do mesmo autor (commit `5bab2ff`,
11/10/2026), licenciado sob AGPL-3.0-only. As alterações feitas na cópia estão
descritas no cabeçalho de cada arquivo e no histórico deste repositório.

## Empacotamento

O instalador (`empacotamento/`: montagem com Python embarcado, lock com
hashes, CRT app-local, fumaça no Python embarcado, script do Inno Setup,
Sandbox e conferência pré-publicação) é adaptação do empacotamento do
**Ulpiano**, do mesmo autor, licenciado sob AGPL-3.0-only. O que é do Ulpiano
(Claude Code, DirectML, verificação de versão, tarefa agendada, skills) ficou
de fora.
