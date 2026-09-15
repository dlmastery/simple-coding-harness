```openui
root = Stack([title, table, statusTag], "column", "m")
title = TextContent("Lemonade Stand Report: Top 3 Flavours", "large-heavy")
table = Table([Col("Flavour", flavours), Col("Sales", sales, "number")])
flavours = ["Classic Lemon", "Strawberry", "Mint Lime"]
sales = [150, 120, 90]
statusTag = Tag("Operating Smoothly", null, "md", "success")
```