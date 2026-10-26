# Bike demand data

We use the hourly table from [UCI Bike Sharing](https://archive.ics.uci.edu/dataset/275/bike+sharing+dataset), donated by Hadi Fanaee-T. It describes Capital Bikeshare rentals in 2011 and 2012. Source attribution: Fanaee-T, H. and Gama, J., *Event labeling combining ensemble detectors and background knowledge*, 2014. The UCI catalogue supplies the data under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

Downloaded 20 September 2026 from UCI. The original archive, hourly and daily tables, and original README are retained in [source](source/Readme.txt). The course adds task and split rules; it does not alter these source files.

| File | SHA-256 |
|---|---|
| `source/bike-sharing.zip` | `b70182d0d0508e9abbb79306ce5c0cec34869000f8220175ac83d11dbe845401` |
| `source/hour.csv` | `e03de4ee4ef4dc376ac6e04bf829673c6269e8eba5c60fa121640fa2f829504f` |

The executable inspection report determines the actual row count, missing values, duplicate rows, dates, and arithmetic relation between rental counts. Do not substitute a catalogue row count for that check.

## Prediction question

Estimate hourly rental count from calendar fields and observed weather. This is a retrospective prediction exercise. Observed weather is not necessarily available when making an advance demand forecast. The task does not support that stronger claim.

Target: `cnt`. Unit: rentals in one recorded hour. Use mean absolute error (MAE), in rentals per hour. Smaller is better. Predicting a negative count is invalid; supplied regressors clip predictions at zero.

Exclude `casual`, `registered`, `instant`, raw `dteday`, and the target from model inputs. The first two are components of the target. The identifier and raw date are excluded by this teaching contract. Calendar information is supplied through explicit fields.

Training: 2011. Selection: January–June 2012. Final evaluation: July–December 2012. The supplied source is public and readable by the agent. These are fixed data roles, **not a secret test boundary**. Reserve a separate inaccessible evaluation service for a stronger independent test.

The data describes one service in a limited period. It cannot establish general performance for other cities or modern transport systems. Missing hours also mean that a one-row shift is not necessarily a one-hour lag. Later forecasting exercises must handle that explicitly.
