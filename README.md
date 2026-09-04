# Renewable Generation Forecasting Tool — ERCOT (Texas)

This project uses historical weather data — sunlight, wind speed, cloud cover, and temperature — from the ERCOT (Texas) grid to predict how much wind and solar power was generated each hour. It then uses those predictions to look at how prepared the grid is for how much that generation swings around.

One note on scope: this project uses historical weather observations to test whether weather predicts generation — it's not yet a live forecasting tool. That said, the same models could plausibly be extended to run on forecast data (like a 24-hour-ahead weather forecast) instead of historical observations, which is what a deployable forecasting tool would actually need. That extension wasn't tested here — see Limitations for what it would take.

**Author:** Fabrizzio Cuanalo
**Repo:** [renewable-generation-forecasting](https://github.com/fabrizziocuanalor-boop/renewable-generation-forecasting)

## Executive Summary

Solar and wind are different problems for the Texas power grid.

Solar changes a lot, especially around sunrise and sunset, but we can generally predict when those changes will happen. So ERCOT can prepare for them ahead of time.

Wind doesn't follow a predictable daily schedule. It can change because weather systems move around Texas. So ERCOT needs to keep resources available for unexpected wind changes.

To test this, I built two regression models — one predicting wind generation, one predicting solar generation — using weather data from 8 Texas locations across 2021-2023, trained on 2021-2022 and tested on unseen 2023 data. The solar model explains about 58% of solar's variation (R² = 0.582). The wind model explains about 26% (R² = 0.264), after testing two different explanations for why wind is harder to predict — the physical curve of how wind speed relates to turbine output, and how many weather locations were used. The second explanation turned out to matter more (see Model Results).

Along the way, three things came up that were as valuable as the models themselves: a 6-hour timezone mismatch between the two data sources that I found and fixed, a confusing negative number in the solar model that a standard statistical test missed, and the test that showed why wind is harder to predict than solar. All three are documented below as they actually happened, including the parts that didn't work, because that's a more honest picture of how the project came together than just the final numbers.

In our data, roughly 95% of hourly wind changes were below about 2,376 MWh. That number could be used as a starting benchmark for thinking about reserve needs, but it shouldn't be interpreted as ERCOT's actual required reserve amount — real reserve planning depends on a lot more than renewable variability alone. We also noticed that the biggest winter solar swings became larger each year across our 3 years of data. Increasing solar capacity in Texas could explain this, but three years isn't enough data to prove it.

## Data Sources

| Source | What | Coverage |
|---|---|---|
| [NREL NSRDB (GOES Aggregated v4.0.0)](https://developer.nlr.gov/docs/solar/nsrdb/) | Hourly sunlight (GHI), wind speed, cloud type, temperature | 8 Texas locations, 2021–2023 |
| [EIA API v2](https://www.eia.gov/opendata/) — `electricity/rto/fuel-type-data` | Hourly ERCOT wind & solar generation (MWh) | ERCOT (respondent `ERCO`), 2021–2023 |

Two different data sources were needed because no single source publishes both weather and generation data together. NREL is a US research lab that runs NSRDB, a satellite-based weather database. EIA is the US agency that tracks energy production, including hourly generation broken down by fuel type, collected from grid operators like ERCOT.

**Locations:** Midland, Sweetwater, Fort Stockton, Amarillo, Abilene, Lubbock, Big Spring, McCamey. We started with the first 4 and later added the other 4 after testing showed that more locations improved the wind model (see Model Results below) — ERCOT's wind farms are spread across a huge area of Texas, so a handful of single weather readings only goes so far in representing the whole fleet.

**Final merged dataset:** 210,192 hourly rows (8 locations × ~26,274 hours each) — `data/final_dataset.csv`.

## Methodology

1. **Collection:** Scripts (`download_weather.py`, `download_generation.py`) pull weather and generation data from each API. EIA only returns 5,000 rows per request, so the generation script loops through multiple requests per year to get complete data.
2. **Merge:** Weather and generation data are matched up by timestamp (`build_dataset.py`). ERCOT reports generation for the whole grid, not by location, so each location's weather is paired with the same system-wide generation numbers.
3. **Modeling:** Separate regression models for wind and solar. Trained on 2021-2022, tested on 2023 — split by time rather than randomly, so the model is only ever tested on data it hasn't seen, from a period after everything it learned from.
4. **Grid analysis:** Hour-to-hour changes in generation are used as a stand-in for how much backup capacity ERCOT needs to keep ready.

## How the Project Actually Came Together

The final version of this project wasn't planned out from the start — it came from following up on things that looked wrong or unexplained along the way.

1. A first version used only 4 weather locations, as a starting point.
2. While checking the results, solar generation showed up at 8-9 PM in December, which isn't physically possible — the sun isn't up then. Digging into why led to finding a 6-hour timestamp mismatch: the generation data was in UTC time, while the weather data was in Texas local time. Fixing this made both models more accurate.
3. After that fix, the wind model was still noticeably less accurate than the solar model. Two possible reasons were tested directly instead of guessed at: whether the model needed to account for the curved (not straight-line) relationship between wind speed and power output, and whether 4 weather locations were enough to represent ERCOT's spread-out wind farms.
4. Adding a "wind speed cubed" input (to capture that curve) barely changed the result. Adding 4 more weather locations (8 total) made a bigger difference. That pointed to location coverage as the bigger issue, though it's not fully proven (see Limitations).
5. Separately, one of the solar model's numbers (sunlight's effect on output) came out negative, which doesn't make physical sense. Removing other variables one at a time didn't explain it. Running a standard statistical test (VIF) for this exact problem said there was no issue — which contradicted what the manual testing suggested. Plotting sunlight against hour of day explained the disagreement: sunlight follows a curved, hill-shaped pattern across the day, and the standard test only catches straight-line relationships, so it missed this one.

This isn't a complete list of every dead end, but it reflects how the project actually moved forward — one specific, checkable question at a time.

## Model Results

| Model | Inputs | Locations | Average Error (MWh) | R² |
|---|---|---|---|---|
| Wind | Wind Speed, Wind Speed³, Temperature, hour, month | 4 | 4,540 | 0.243 |
| Wind | Wind Speed, Wind Speed³, Temperature, hour, month | 8 | 4,464 | 0.264 |
| Solar | Sunlight (GHI), Cloud Type, Temperature, hour, month | 8 | 1,993 | 0.582 |

![Wind vs solar model accuracy comparison](images/wind_vs_solar_accuracy.png)

Solar's model is noticeably more accurate than wind's, and figuring out why was more useful than just reporting the gap.

Wind turbines produce power roughly proportional to wind speed cubed, not wind speed directly — power increases slowly at low wind speeds, then much faster, then levels off once a turbine hits its max output. A straight-line model can't naturally capture that curve, so it seemed like a likely reason wind was harder to predict.

Two explanations were tested side by side, rather than picking one and assuming it was right:

1. **The curved relationship between wind speed and power.** Adding wind speed cubed as an extra input only moved R² from 0.237 to 0.243 — barely anything. This ruled out the curve as the main problem.
2. **Not enough weather locations to represent ERCOT's spread-out wind farms.** Going from 4 locations to 8 (adding Abilene, Lubbock, Big Spring, and McCamey) moved R² from 0.243 to 0.264 — a bigger jump than the cubic term gave us. This points to location coverage as the more significant limitation of the two.

This is evidence, not full proof. Only one specific set of 4 additional locations was tested, so it's possible the improvement partly reflects those particular towns rather than "more coverage" as a general rule. A more rigorous test would try different sets of added locations, or weight locations by how much wind capacity is actually installed nearby.

Solar's R² barely moved with the extra locations (0.579 → 0.582), which makes sense — sunlight tends to be more similar across a region at the same time of day than wind speed is, so solar was never as limited by having only a few locations in the first place.

![Solar generation: actual vs predicted, sample week June 2023](images/solar_prediction_chart.png)

*The model correctly follows the daily on/off solar pattern but tends to under-predict the peak. That's what an R² of 0.579 actually looks like: pointed in the right direction, but not precise.*

## Data Quality Investigations

### 1. Timezone mismatch (found and fixed)

While looking at an unusually large swing in the data, solar generation appeared to peak around 8-9 PM — which isn't possible in December, when the sun sets by early evening. This pointed to a timezone mismatch: the weather data was explicitly pulled in Texas local time, and the pattern looked exactly like what you'd see if the generation data were actually in UTC (6 hours ahead of Texas in winter), even though nothing in the raw data or documentation stated this directly. To confirm the hypothesis rather than just assume it, I shifted the generation timestamps back 6 hours and checked whether solar started peaking at a physically sensible time — it did, moving from an impossible 8-9 PM peak to a normal midday peak. That confirmation, not an official statement from EIA, is what verified the fix. Applying the 6-hour shift in `build_dataset.py` improved both models:

| | Before fix | After fix |
|---|---|---|
| Solar R² | 0.467 | 0.579 |
| Wind R² | 0.185 | 0.237 |
| Sunlight's effect on solar output | −4.14 (wrong direction) | +7.00 (correct direction) |

### 2. A confusing number in the solar model

Even after the timezone fix, the solar model's number for sunlight's effect on output would sometimes come out negative — saying "more sunlight, less power," which makes no sense. The likely reason: sunlight and hour-of-day both roughly describe the same thing (is it the middle of the day), so the model has trouble telling which one deserves credit.

This was checked two ways. First, manually: removing hour-of-day from the model dropped its accuracy a lot (R² fell from 0.467 to 0.111), showing that hour genuinely carries useful information. Removing cloud cover instead barely changed anything, ruling that out as the cause.

Second, formally: a standard statistical test for this exact problem (called VIF) came back showing no issue at all — every score was low, which seemed to contradict the manual finding. Plotting sunlight against hour of day explained why: the relationship is a curve (rising through the morning, peaking at noon, falling in the evening), not a straight line. The standard test only catches straight-line relationships, so it missed a real, curved overlap that the manual testing had already picked up on.

The takeaway: hour-of-day stays in the model because it's genuinely useful, and the sunlight coefficient specifically shouldn't be read on its own — but the model's overall accuracy score is still a fair measure of how well it works.

![GHI vs hour of day, showing the non-linear daily curve](images/ghi_vs_hour_check.png)

## Grid Preparedness Findings

- Combined wind and solar generation averaged about **14,521 MWh per hour** across 2021-2023, with a lot of spread around that average (standard deviation of 6,171 MWh).
- The single biggest hour-to-hour drop in the whole dataset was **−10,318 MWh**, at sunset on December 29, 2023 — mostly explained by solar's normal evening ramp-down (13,213 → 0 MWh over four hours), plus a same-day dip in wind.
- Looking at wind on its own during daytime hours only (9 AM-5 PM, avoiding sunrise/sunset effects), its typical hour-to-hour swing (standard deviation of 1,035 MWh) is nearly identical to its swing across all hours of the day (1,135 MWh). In other words, wind is about equally variable no matter the time of day — it doesn't follow a schedule the way solar does.

**What this means:** solar's biggest swings happen at a known time every day, so ERCOT can schedule backup power in advance. Wind's swings can happen at any hour, so backup capacity for wind needs to be ready at all times, not scheduled around a pattern.

## Recommendation

Wind and solar fail in different ways, so they probably shouldn't be planned for the same way.

For wind: in this data, 95% of hourly swings stayed under about 2,376 MWh. That number is a useful starting point for thinking about how much backup capacity to keep ready — but it isn't a full answer. Real reserve planning depends on a lot more than renewable variability alone, including demand uncertainty, other generators going offline, and transmission limits, none of which this project looked at. The rarer 5% of hours with bigger swings (like fast-moving weather fronts) would need separate planning beyond a standard day-to-day reserve.

For solar: since its big swings happen at a predictable time (sunset and sunrise), backup capacity can be scheduled in advance rather than held on standby constantly. Typical swings were somewhat bigger in summer than winter in this data, likely because longer days mean more total solar output available to swing around. One thing worth watching: the single biggest winter solar drop got larger every year across our 3 years of data (2021: −3,787 MWh, 2022: −4,923 MWh, 2023: −7,455 MWh). This lines up with Texas adding a lot of solar capacity over that period, but three years isn't enough data to call it a confirmed trend — it's worth checking again with more years of data before treating it as reliable.

## Limitations

- This project uses historical weather observations, not live weather forecasts. It tests whether weather predicts generation, not whether a deployable forecasting tool works with real forecast data (which has its own errors). The same models could plausibly extend to a real forecasting tool by swapping in forecast data instead of historical observations, and checking accuracy at different forecast lead times — that extension is a natural next step, not something ruled out by this project.
- Two explanations for wind's low accuracy were tested directly: the curved wind-speed-to-power relationship (barely helped) and limited location coverage (helped more). This points to location coverage as the bigger factor, but it's not fully proven — only one set of 4 additional locations was tested, so part of the improvement could be specific to those towns rather than "more coverage" in general. Wind's R² of 0.264 still leaves most of its variation unexplained; getting further would likely need even broader coverage, weighting locations by installed wind capacity, or a model that can handle curves.
- The 6-hour timezone fix doesn't account for daylight saving time (Texas shifts to UTC-5 part of the year), so there's a small remaining mismatch during those months.
- The solar model's sunlight coefficient shouldn't be read on its own, due to the overlap with hour-of-day described above — only the model's overall accuracy score should be trusted.
- The apparent year-over-year growth in winter solar swings is based on only 3 data points and shouldn't be treated as a confirmed trend without more years of data.

## Repository Structure

```
data/
  raw/                       # Original downloaded weather & generation CSVs
  final_dataset.csv          # Merged, cleaned dataset used for modeling
images/
  solar_prediction_chart.png       # Actual vs predicted solar generation
  wind_vs_solar_accuracy.png       # Wind vs solar R² comparison
  ghi_vs_hour_check.png            # Sunlight vs hour of day (the curve)
download_weather.py          # Pulls NREL weather data
download_generation.py       # Pulls EIA generation data (handles pagination)
build_dataset.py             # Merges weather + generation into final_dataset.csv
explore_dataset.py           # Data quality checks
train_model.py                # Trains and evaluates the wind & solar models
grid_analysis.py             # Grid variability analysis
```

## How to Run This

**You'll need:** Python 3, plus free API keys from [EIA](https://www.eia.gov/opendata/register.php) and [NREL/NLR](https://developer.nlr.gov/signup/).

1. **Clone the repo and install what it needs:**
   ```
   git clone git@github.com:fabrizziocuanalor-boop/renewable-generation-forecasting.git
   cd renewable-generation-forecasting
   pip install requests python-dotenv pandas scikit-learn matplotlib statsmodels
   ```

2. **Add your API keys.** Create a file named `.env` in the project folder containing:
   ```
   EIA_API_KEY=your_eia_key_here
   NREL_API_KEY=your_nrel_key_here
   ```

3. **Run the scripts in order:**
   ```
   python download_weather.py       # Downloads weather data (8 locations x 3 years)
   python download_generation.py    # Downloads ERCOT generation data (2 fuel types x 3 years)
   python build_dataset.py          # Merges everything into data/final_dataset.csv
   python explore_dataset.py        # Prints data quality checks
   python train_model.py            # Trains wind & solar models, saves charts
   python grid_analysis.py          # Runs the grid variability analysis
   ```

Each script prints its own progress as it runs. The whole thing takes a few minutes, mostly spent waiting on the download scripts.

## Glossary

**Statistics / modeling terms**
- **Regression model** — a model that predicts a number (like megawatt-hours) from other numbers (like wind speed), by fitting a formula to past data.
- **Linear regression** — the simplest kind of regression, which assumes a straight-line relationship between inputs and output.
- **Coefficient** — the number a model assigns to an input, showing how much that input affects the prediction.
- **R² (R-squared)** — a score from 0 to 1 showing what share of the outcome's ups and downs the model's inputs actually explain.
- **Average error (MAE)** — on average, how far off the model's predictions were, in real units.
- **Training set / test set** — the training set is what the model learns from; the test set is separate, unseen data used to check if it actually works.
- **Data leakage** — when information from the test set accidentally sneaks into training, making a model look better than it really is.
- **Multicollinearity** — when two or more inputs are closely related to each other, which can make a model's individual numbers unreliable even if its overall predictions are fine.
- **VIF (Variance Inflation Factor)** — the standard test for multicollinearity. It only catches straight-line relationships between inputs.
- **Nonlinear relationship** — a relationship where the rate of change isn't constant, unlike a straight line (a curve, basically).

**Energy / domain terms**
- **ERCOT** — the organization that runs the electric grid for most of Texas.
- **Balancing authority** — an organization responsible for keeping electricity supply and demand matched at all times across its grid.
- **GHI (Global Horizontal Irradiance)** — a measurement of sunlight intensity, used here as the main predictor of solar output.
- **MWh (Megawatt-hour)** — a unit of electricity: one megawatt of power sustained for one hour.
- **UTC (Coordinated Universal Time)** — a global time standard many data systems default to, instead of local time zones.
- **Pagination** — when an API limits how many results it gives per request, so you have to ask multiple times to get everything.

## Tools

Python, pandas, scikit-learn, statsmodels, matplotlib, NREL NSRDB API, EIA API v2.
