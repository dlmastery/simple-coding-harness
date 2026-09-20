# Technical schematic review gallery

Original Mermaid diagrams. These are not Imagen-generated illustrations.

## 07.07 · Learn what self-play does and does not provide

```mermaid
%%{init: {"theme":"base","themeVariables":{"background":"#ffffff","primaryColor":"#eef5fb","primaryTextColor":"#172b3a","primaryBorderColor":"#45667d","lineColor":"#45667d","secondaryColor":"#fff3d9","tertiaryColor":"#e9f6f0","fontFamily":"Arial"}}}%%
flowchart LR
A["Proposer role"] -->|challenge| B["Critic role"]
B -->|response| A
A --> C["Saved exchange"] --> D["Executable rule check"]
```

*Read the diagram:* This role exchange illustrates interaction. It contains no training update and does not establish self-play learning.
