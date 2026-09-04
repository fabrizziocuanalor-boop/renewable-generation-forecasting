# Renewable Generation Forecasting Tool (ERCOT, Texas)

## Overview

This project uses historical weather data (sunlight, wind speed, cloud cover, temperature) from Texas to predict how much wind and solar power ERCOT, the organization that runs the Texas power grid, generated each hour. It then uses those predictions to look at how prepared the grid is for how much that generation swings around. I built this to test a specific question: can weather alone tell us enough to plan around renewable generation's ups and downs, and if not, why not?

Full technical details, data sources, setup instructions, and a glossary of terms are in [`docs/technical_notes.md`](docs/technical_notes.md). This README focuses on what I built, what I found, and how the project actually came together.

## Why This Problem Matters

Solar and wind are different problems for a power grid. Solar changes a lot, especially around sunrise and sunset, but those changes happen on a predictable daily schedule, so a grid operator can plan for them in advance. Wind doesn't follow a schedule. It changes because weather systems move through an area, which means a grid operator has to keep resources ready for wind changes at any hour, not just at known times. Understanding how big these swings are, and how differently wind and solar behave, matters for deciding how much backup power capacity ERCOT needs to keep on hand.

## What I Built

Using weather data from 8 Texas locations across 2021-2023 and matching hourly ERCOT generation data, I built two regression models, one predicting wind generation and one predicting solar generation. Both were trained on 2021-2022 and tested on 2023, data the models never saw during training, to check they actually generalize rather than just memorize the past. I then used the models' results to look at how much combined wind and solar generation swings hour to hour, and what that implies for how ERCOT might plan reserve capacity.

## How the Project Actually Came Together

The final version of this project wasn't planned out from the start. It came from following up on things that looked wrong or unexplained along the way.

1. A first version used only 4 weather locations, as a starting point.
2. While checking the results, solar generation showed up at 8-9 PM in December, which isn't physically possible; the sun isn't up then. Digging into why pointed to a 6-hour timestamp mismatch: the pattern looked exactly like what you'd expect if the generation data were in UTC while the weather data was in Texas local time. Shifting the timestamps and checking that solar started peaking at a normal midday hour confirmed it. Applying that fix made both models noticeably more accurate (solar R² went from 0.467 to 0.579, wind from 0.185 to 0.237).
3. After that fix, the wind model was still noticeably less accurate than the solar model. Two possible reasons were tested directly instead of guessed at: whether the model needed to account for the curved, not straight-line, relationship between wind speed and power output, and whether 4 weather locations were enough to represent ERCOT's spread-out wind farms.
4. Adding a "wind speed cubed" input to capture that curve barely changed the result (R² moved from 0.237 to 0.243). Adding 4 more weather locations, 8 total, made a bigger difference (R² moved to 0.264). That pointed to location coverage as the bigger issue, though it isn't fully proven with just one added set of locations (see Limitations).
5. Separately, one of the solar model's numbers, sunlight's effect on output, came out negative, which doesn't make physical sense. Removing other variables one at a time didn't explain it. Running a standard statistical test (VIF) for this exact problem said there was no issue, which contradicted the manual testing. Plotting sunlight against hour of day explained the disagreement: sunlight follows a curved, hill-shaped pattern across the day, and the standard test only catches straight-line relationships, so it missed this one.

This isn't a complete list of every dead end, but it reflects how the project actually moved forward, one specific, checkable question at a time.

## Results

| Model | Inputs | Locations | Average Error (MWh) | R² |
|---|---|---|---|---|
| Wind | Wind Speed, Wind Speed³, Temperature, hour, month | 4 | 4,540 | 0.243 |
| Wind | Wind Speed, Wind Speed³, Temperature, hour, month | 8 | 4,464 | 0.264 |
| Solar | Sunlight (GHI), Cloud Type, Temperature, hour, month | 8 | 1,993 | 0.582 |

![Wind vs solar model accuracy comparison](images/wind_vs_solar_accuracy.png)

Solar's model is noticeably more accurate than wind's. Wind turbines produce power roughly proportional to wind speed cubed, not wind speed directly, so a straight-line model naturally struggles to capture that curve. But testing showed the curve wasn't actually the main problem: adding wind speed cubed barely moved the score. Expanding from 4 to 8 weather locations moved it more, pointing to insufficient coverage of ERCOT's spread-out wind fleet as the bigger limitation of the two, not full proof, but real evidence. Solar's score barely moved with more locations, which makes sense since sunlight is more uniform across a region than wind speed is, so solar was never as limited by having only a few locations.

![Solar generation: actual vs predicted, sample week June 2023](images/solar_prediction_chart.png)

*The model correctly follows the daily on/off solar pattern but tends to under-predict the peak. That's what an R² of 0.579 actually looks like: pointed in the right direction, but not precise.*

The same negative-coefficient investigation is detailed in `docs/technical_notes.md`, including the VIF test and the chart that resolved the contradiction.

![GHI vs hour of day, showing the non-linear daily curve](images/ghi_vs_hour_check.png)

## What This Means for the Grid

Combined wind and solar generation averaged about 14,521 MWh per hour across 2021-2023, with a lot of spread around that average (standard deviation of 6,171 MWh). The single biggest hour-to-hour drop in the dataset was 10,318 MWh, at sunset on December 29, 2023, mostly explained by solar's normal evening ramp-down plus a same-day dip in wind. Looking at wind on its own during daytime hours only, its typical swing is nearly identical to its swing across all hours of the day. Wind is about equally variable no matter the time of day; it doesn't follow a schedule the way solar does.

**Recommendation:** wind and solar fail in different ways, so they probably shouldn't be planned for the same way. For wind, 95% of hourly swings in this data stayed under about 2,376 MWh. That number is a useful starting benchmark for thinking about backup capacity, but it isn't a full answer since real reserve planning depends on a lot more than renewable variability alone (demand uncertainty, other generators going offline, transmission limits), none of which this project looked at. The rarer 5% of hours with bigger swings, like fast-moving weather fronts, would need separate contingency planning. For solar, since its big swings happen at a predictable time, backup capacity can be scheduled in advance rather than held constantly on standby. Typical swings were somewhat bigger in summer than winter, likely because longer days mean more total solar output available to swing around. One thing worth watching: the single biggest winter solar drop got larger every year across the 3 years studied (2021: 3,787 MWh, 2022: 4,923 MWh, 2023: 7,455 MWh), which lines up with Texas adding a lot of solar capacity over that period, but three years isn't enough data to call it a confirmed trend.

## Limitations

- This project uses historical weather observations, not live weather forecasts. It tests whether weather predicts generation, not whether a deployable forecasting tool works with real forecast data, which has its own errors. The same models could plausibly extend to a real forecasting tool by swapping in forecast data instead of historical observations. That extension is a natural next step, not something ruled out here.
- The evidence that limited location coverage is wind's bigger limitation isn't a fully isolated causal test. Only one set of 4 additional locations was tried, so part of the improvement could be specific to those towns rather than "more coverage" in general. Wind's R² of 0.264 still leaves most of its variation unexplained.
- The 6-hour timezone fix doesn't account for daylight saving time, so there's a small remaining mismatch during those months.
- The solar model's sunlight coefficient shouldn't be read on its own, due to its overlap with hour-of-day; only the model's overall accuracy score should be trusted.
- The apparent year-over-year growth in winter solar swings is based on only 3 data points and shouldn't be treated as a confirmed trend without more years of data.

More detail on data sources, setup instructions, the repository structure, and a glossary of terms used above are in [`docs/technical_notes.md`](docs/technical_notes.md).

## Tools

Python, pandas, scikit-learn, statsmodels, matplotlib, NREL NSRDB API, EIA API v2.
