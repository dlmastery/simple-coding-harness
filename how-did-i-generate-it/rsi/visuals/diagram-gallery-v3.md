# Technical schematic review gallery

Original Mermaid diagrams. These are not Imagen-generated illustrations.

## 00.01 · Meet the prediction task

```mermaid
%%{init: {"theme":"base","themeVariables":{"background":"#ffffff","primaryColor":"#eef5fb","primaryTextColor":"#172b3a","primaryBorderColor":"#45667d","lineColor":"#45667d","secondaryColor":"#fff3d9","tertiaryColor":"#e9f6f0","fontFamily":"Arial"}}}%%
flowchart TD
A["Calendar + weather"] --> B["Predicted rentals"]
C["casual + registered"] --> D["Actual rentals"]
B --> E["Compare"]
D --> E
```

*Read the diagram:* Predict the hourly total from allowed inputs. The two component counts already contain the answer.
