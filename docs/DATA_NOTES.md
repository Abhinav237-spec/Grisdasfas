# Data notes (Sprint 1 exploration)

Raw files: `data/raw/fuelhh_wind.json` (actuals) and `data/raw/windfor.json` (forecasts), downloaded from the Elexon BMRS API.
All figures below come from `python scripts/explore.py` and `python scripts/run_analysis.py` on those files.

## What the files contain

| | FUELHH wind (actuals) | WINDFOR (forecasts) |
|---|---|---|
| Fields | dataset, publishTime, startTime, settlementDate, settlementPeriod, fuelType, generation | dataset, publishTime, startTime, generation |
| Resolution | 30 minutes | **1 hour** (startTime always on the hour) |
| Range | 2 Jan 00:00 to 1 Feb 23:30 UTC | published 25 Dec 02:30 to 31 Jan 22:30 UTC; targets 24 Dec to 2 Feb |
| Rows | 1,488 (31 days x 48, none missing) | 22,192 |
| Quality | no duplicates, nulls or negatives | no duplicates or nulls |
| Typical level | mean 11,284 MW, peak 17,805 MW | mean 12,353 MW (all forecasts) |

## How forecasts are published

- Eight forecast runs per day, always at 02:30, 04:30, 07:30, 09:30, 11:30, 15:30, 18:30 and 22:30 UTC (one run slipped by 5 minutes). 304 runs in total.
- Each run covers targets from about 25 hours in the past to about 66 hours ahead (median 73 hourly targets per run).
- About 20 percent of forecast rows (4,561) have a `publishTime` after their `startTime`. These are not usable for decisions and the cutoff rule excludes them. In the lead-time analysis only rows with a lead time of zero or more are used.

## Decisions taken because of this

1. **Compare at hourly resolution.** Each forecast hour is compared with the mean of the two FUELHH half-hours in that hour (start of hour and +30 minutes). Alternative alignments change the MAE by under 4 percent (2,002 to 2,080 MW), so the choice is not material. Result: 24 comparisons per delivery day, 744 in total.
2. **Decision cutoff stays at 09:00 UK time on the day before delivery** and is configurable. With 09:00 the latest usable run is 07:30, so decision lead times are 16.5 to 39.5 hours. All 31 delivery days (2 Jan to 1 Feb 2026) have a forecast for all 24 hours.
3. **Delivery days are 2 Jan to 1 Feb**, because decisions made in January are for the following day.
4. **Actuals can be re-published**, so the loader keeps the latest publication of each half-hour (no duplicates were present in this file).

## Findings (cutoff 09:00, 744 hours)

| Metric | Value |
|---|---|
| MAE | 2,039 MW (18.1 percent of mean actual, 11.5 percent of peak) |
| RMSE | 2,505 MW |
| Bias (forecast minus actual) | **+1,748 MW** |
| Error scatter (standard deviation) | 1,794 MW |
| Hours where the forecast was too high | 85 percent |
| Absolute error P50 / P90 / P95 | 1,671 / 4,098 / 5,283 MW |

- **The forecast is systematically higher than FUELHH actuals** by about 15.5 percent (sum of forecast over sum of actual is 1.155). The bias is present at every lead time, even for forecasts published less than 6 hours before the target (+1,453 MW), and in forecasts published after the target hour. So most of it is not a lead-time effect. A plausible explanation (not verified here) is that the two datasets cover different wind capacity, for example metered transmission wind versus a wider total. It should be described as an observed offset, not as a cause.
- **Bias-corrected, the typical error is smaller.** Removing the mean bias leaves an MAE of about 1,376 MW (in-sample).
- **Accuracy gets worse with lead time, but gently.** MAE rises from 1,686 MW (0 to 6 hours) to 2,070 MW (30 to 36 hours) and 2,317 MW (48 to 72 hours).
- **Bias is larger at night and at high wind.** Hourly bias peaks at about +2,350 MW between 03:00 and 06:00 UK time and is lowest, about +1,250 MW, mid-afternoon. In the top third of wind hours the bias is +2,283 MW against +1,451 MW in the bottom third.
- **Worst days are almost entirely over-forecasts:** 28 Jan (MAE 5,375 MW), 12 Jan (4,868), 11 Jan (4,802), 21 Jan (3,658), 27 Jan (3,479). On 87 percent of days the average error is positive.
- **Safety margin:** the 90th percentile of signed error is about 4,098 MW. Subtracting it from the forecast gave an actual at or above that figure in 89.9 percent of hours. This is in-sample, so it is optimistic for future months.

## Cutoff sensitivity

| Cutoff (UK) | Latest run used | MAE (MW) |
|---|---|---|
| 08:00 or 09:00 | 07:30 | 2,039 |
| 09:30 or 10:00 | 09:30 | 2,013 |
| 12:00 | 11:30 | 1,901 |
| 16:00 | 15:30 | 1,873 |

A cutoff before about 07:30 on D-1 leaves some late-evening hours of the delivery day with no forecast.

## Limitations to state in the app and video

- One month of data, so the margin and breakdowns are estimated in-sample.
- National totals, wind only, FUELHH as the definition of actual.
- The 09:00 cutoff is an assumption, not taken from the brief.
