# Synthetic demand fixture

Predict a synthetic continuous demand value from generated calendar and weather measurements. Units are constructed demand units per observation. This is not a real rental dataset or a future-weather forecast. Seed 61005; 480 IID generated rows; fixed split 280/100/100. Training rows alone fit preprocessing. Calendar features: sin_hour, cos_hour, weekend. Weather group: temperature, humidity. Source generator is in the retained driver. The host can inspect all labels and the generating formula; evaluation is a cooperative boundary, not secrecy.
