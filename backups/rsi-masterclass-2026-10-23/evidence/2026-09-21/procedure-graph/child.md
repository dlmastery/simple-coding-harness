# Procedure graph

| Node | Outcome | Next |
|---|---|---|
| inspect | valid | domain |
| inspect | invalid | diagnose |
| domain | valid | fit |
| domain | invalid | diagnose |
| fit | done | report |
| report | done | stop |
| diagnose | done | stop |
