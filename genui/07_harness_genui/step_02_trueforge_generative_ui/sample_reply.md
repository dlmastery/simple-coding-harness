```openui
root = Stack([title, topFlavoursTable, revenueLineChartCard, kpiStack, statusTag, closingText], "column", "l", "center")

title = TextContent("Lemonade Stand Report", "large-heavy")

topFlavoursTable = Card([
  CardHeader("Top 3 Flavours - Cups Sold & Price"),
  Table([
    Col("Flavour", ["Classic Lemon", "Strawberry", "Mint"]),
    Col("Cups Sold", [150, 120, 100], "number"),
    Col("Price per Cup ($)", [1.50, 1.75, 1.60], "number")
  ])
])

revenueLineChartCard = Card([
  CardHeader("Weekly Revenue Over Four Weeks"),
  LineChart(
    ["Week 1", "Week 2", "Week 3", "Week 4"],
    [Series("Revenue ($)", [225, 260, 240, 280])],
    "linear",
    "Week",
    "Revenue ($)"
  )
])

kpiStack = Stack([
  Card([TextContent("Total Cups Sold", "small"), TextContent("370", "large-heavy")]),
  Card([TextContent("Average Price per Cup ($)", "small"), TextContent("1.62", "large-heavy")])
], "row", "xl", "center", "evenly")

statusTag = Tag("Performance", null, "md", "success")

closingText = TextContent("Sales are strong and trending upward, keep focusing on the top flavours to maximize revenue.", "default")
```