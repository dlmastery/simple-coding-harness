# A different task: tomorrow's noon demand

This is a proposed task brief, separate from the executed retrospective experiment. No forecast model is trained here.

Make the forecast at noon on the previous day. Estimate total rentals during tomorrow's 12:00–12:59 hour in the source service's local time. Target unit is rentals in that hour; evaluate MAE in the same units. State the timezone and daylight-saving treatment before acquiring future data.

Calendar fields are known at the forecast origin: target date, hour, weekday and calendar season. Holiday and working-day flags require the relevant published calendar. Tomorrow's observed temperature, apparent temperature, humidity, wind and weather category are not yet known. Tomorrow's casual/registered counts and total rentals are outcomes, not inputs. An archived table containing those values does not make them available a day earlier.

Begin with calendar-only inputs if testing this new task. Add weather only after obtaining forecasts with issue timestamps at or before each historical forecast origin. Keep forecast versions and align their target hours. The supplied hourly CSV has observations, not an archive of historical forecast issues, so the weather extension is blocked by missing task data. Do not fill this gap with the later observations.

Training examples must pair the inputs available at each forecast origin with the subsequent noon outcome. Define chronological development/final periods before fitting, and retain a gap if feature construction or reporting delay requires one. The old all-hours result is not a noon-only forecasting result. Any new split, population or input source creates a new declared experiment with its own reviewed budget; this brief permits zero fits.
