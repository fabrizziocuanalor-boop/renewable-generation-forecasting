# Technical Notes

Supporting detail for the main [README](../README.md): full data sources, methodology, setup instructions, repository structure, a Works Cited list, and a glossary of terms.

## Data Sources

| Source | What | Coverage |
|---|---|---|
| [NREL NSRDB (GOES Aggregated v4.0.0)](https://developer.nlr.gov/docs/solar/nsrdb/) | Hourly sunlight (GHI), wind speed, cloud type, temperature | 8 Texas locations, 2021-2023 |
| [EIA API v2](https://www.eia.gov/opendata/), `electricity/rto/fuel-type-data` | Hourly ERCOT wind and solar generation (MWh) | ERCOT (respondent `ERCO`), 2021-2023 |

Two different data sources were needed because no single source publishes both weather and generation data together. NREL is a US research lab that runs NSRDB, a satellite-based weather database (NREL). EIA is the US agency that tracks energy production, including hourly generation broken down by fuel type, collected from grid operators like ERCOT (EIA).

**Locations:** Midland, Sweetwater, Fort Stockton, Amarillo, Abilene, Lubbock, Big Spring, McCamey. We started with the first 4 and later added the other 4 after testing showed that more locations improved the wind model. ERCOT's wind farms are spread across a huge area of Texas, so a handful of single weather readings only goes so far in representing the whole fleet.

**Final merged dataset:** 210,192 hourly rows (8 locations times approximately 26,274 hours each), saved as `data/final_dataset.csv`.

## Methodology

1. **Collection:** Scripts (`download_weather.py`, `download_generation.py`) pull weather and generation data from each API. EIA only returns 5,000 rows per request, so the generation script loops through multiple requests per year to get complete data.
2. **Merge:** Weather and generation data are matched up by timestamp (`build_dataset.py`). ERCOT reports generation for the whole grid, not by location, so each location's weather is paired with the same system-wide generation numbers.
3. **Modeling:** Separate regression models for wind and solar. Trained on 2021-2022, tested on 2023, split by time rather than randomly, so the model is only ever tested on data it hasn't seen, from a period after everything it learned from. This chronological split, rather than a random one, is the standard approach for time series data, since randomly shuffling would let the model train on data from after the point it's being tested on (Hyndman and Athanasopoulos).
4. **Grid analysis:** Hour-to-hour changes in generation are used as a stand-in for how much backup capacity ERCOT needs to keep ready.

## The Multicollinearity Investigation

Even after the timezone fix, the solar model's number for sunlight's effect on output would sometimes come out negative, saying "more sunlight, less power," which makes no sense. The likely reason: sunlight and hour-of-day both roughly describe the same thing, whether it's the middle of the day, so the model has trouble telling which one deserves credit.

This was checked two ways. First, by hand: removing hour-of-day from the model dropped its accuracy a lot (R² fell from 0.467 to 0.111), showing that hour genuinely carries useful information. Removing cloud cover instead barely changed anything, ruling that out as the cause.

Second, I wanted a more formal way to check this, so I asked Claude what the standard statistical test for this exact problem would be. It pointed me to VIF (Variance Inflation Factor), a test made specifically for spotting this kind of issue and first created by a statistician named Marquardt. Running it came back showing no issue at all, every score was low, which seemed to disagree with what the hand-testing found. Plotting sunlight against hour of day explained why: the relationship between them is a curve, rising through the morning, peaking at noon, falling in the evening, not a straight line. The VIF test only catches straight-line relationships, so it missed a real, curved overlap that the hand-testing had already picked up on.

One more thing worth knowing: the rule we used, that a VIF score above 5 to 10 means there's a problem, isn't an exact law. It's just a common guideline most researchers use, and the right number can actually change depending on the situation (O'Brien). This doesn't change our results, since our VIF scores were low no matter which exact number you use, but it's worth knowing the rule itself isn't as strict as it's often made to sound. This is also the kind of reasoning that combines a few different ideas instead of coming from one clear source, so I used Claude to help check the logic and then read the actual papers myself to make sure it held up, rather than just trusting the explanation.

The takeaway: hour-of-day stays in the model because it's genuinely useful, and the sunlight coefficient specifically shouldn't be read on its own. The model's overall accuracy score is still a fair measure of how well it works.

## Repository Structure

```
data/
  raw/                              # Original downloaded weather and generation CSVs
  final_dataset.csv                 # Merged, cleaned dataset used for modeling
images/
  solar_prediction_chart.png        # Actual vs predicted solar generation
  wind_vs_solar_accuracy.png        # Wind vs solar R² comparison
  ghi_vs_hour_check.png             # Sunlight vs hour of day (the curve)
docs/
  technical_notes.md                # This file
download_weather.py                 # Pulls NREL weather data
download_generation.py              # Pulls EIA generation data (handles pagination)
build_dataset.py                    # Merges weather and generation into final_dataset.csv
explore_dataset.py                  # Data quality checks
train_model.py                      # Trains and evaluates the wind and solar models
grid_analysis.py                    # Grid variability analysis
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
   python train_model.py            # Trains wind and solar models, saves charts
   python grid_analysis.py          # Runs the grid variability analysis
   ```

Each script prints its own progress as it runs. The whole thing takes a few minutes, mostly spent waiting on the download scripts.

## Works Cited

EIA. "API Technical Documentation." *U.S. Energy Information Administration*, www.eia.gov/opendata/documentation.php.

"Effect of Light Intensity." *PVEducation*, www.pveducation.org/pvcdrom/solar-cell-operation/effect-of-light-intensity. Explains that a solar cell's electrical output increases roughly in a straight line with light intensity, the physical basis for treating solar output as closer to linear than wind output in this project.

ERCOT. "Recommendation Regarding 2026 ERCOT Methodologies for Determining Minimum Ancillary Service Requirements." *ERCOT*, 15 Sept. 2025, www.ercot.com/files/docs/2025/09/15/15-Recommendation-regarding-2026-ERCOT-Methodologies-for-Determining-Minimum-Ancillary-Service-Requirements.pdf. Cited as an example that percentile-based sizing of reserves against renewable variability is a real industry approach, not this project's own invention. ERCOT's actual methodology, which sizes certain reserve requirements around the 95th percentile of net load forecast error, is far more detailed than the single calculation used in this project.

Hyndman, Rob J., and George Athanasopoulos. *Forecasting: Principles and Practice*. 3rd ed., OTexts, 2021, otexts.com/fpp3/. See the chapters on time series cross-validation and evaluation, which explain why random train/test splits leak future information into training for time-ordered data like this project's.

Marquardt, Donald W. "Generalized Inverses, Ridge Regression, Biased Linear Estimation, and Nonlinear Estimation." *Technometrics*, vol. 12, no. 3, 1970, pp. 591-612, doi:10.1080/00401706.1970.10488699. The paper credited with introducing the variance inflation factor as a diagnostic.

NREL. "National Solar Radiation Database (NSRDB)." *National Renewable Energy Laboratory*, developer.nlr.gov/docs/solar/nsrdb/.

O'Brien, Robert M. "A Caution Regarding Rules of Thumb for Variance Inflation Factors." *Quality & Quantity*, vol. 41, no. 5, 2007, pp. 673-90, doi:10.1007/s11135-006-9018-6.

United States, Department of Energy, Office of Energy Efficiency and Renewable Energy. "How Do Wind Turbines Work?" *Energy.gov*, www.energy.gov/eere/wind/how-do-wind-turbines-work.

## Glossary

**Statistics and modeling terms**
- **Regression model:** a model that predicts a number (like megawatt-hours) from other numbers (like wind speed), by fitting a formula to past data.
- **Linear regression:** the simplest kind of regression, which assumes a straight-line relationship between inputs and output.
- **Coefficient:** the number a model assigns to an input, showing how much that input affects the prediction.
- **R² (R-squared):** a score from 0 to 1 showing what share of the outcome's ups and downs the model's inputs actually explain.
- **Average error (MAE):** on average, how far off the model's predictions were, in real units.
- **Training set / test set:** the training set is what the model learns from; the test set is separate, unseen data used to check if it actually works.
- **Data leakage:** when information from the test set accidentally sneaks into training, making a model look better than it really is.
- **Multicollinearity:** when two or more inputs are closely related to each other, which can make a model's individual numbers unreliable even if its overall predictions are fine.
- **VIF (Variance Inflation Factor):** the standard test for multicollinearity. It only catches straight-line relationships between inputs.
- **Nonlinear relationship:** a relationship where the rate of change isn't constant, unlike a straight line, essentially a curve.

**Energy and domain terms**
- **ERCOT:** the organization that runs the electric grid for most of Texas.
- **Balancing authority:** an organization responsible for keeping electricity supply and demand matched at all times across its grid.
- **GHI (Global Horizontal Irradiance):** a measurement of sunlight intensity, used here as the main predictor of solar output.
- **MWh (Megawatt-hour):** a unit of electricity, one megawatt of power sustained for one hour.
- **UTC (Coordinated Universal Time):** a global time standard many data systems default to, instead of local time zones.
- **Pagination:** when an API limits how many results it gives per request, so you have to ask multiple times to get everything.
- **Net load:** in grid planning, demand minus variable renewable generation (wind and solar); this is the load that dispatchable resources actually have to cover.
