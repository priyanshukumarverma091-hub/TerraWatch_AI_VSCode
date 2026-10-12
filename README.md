TerraWatch AI
Satellite-Based Vegetation Monitoring and Historical Analysis

TerraWatch AI is an AI-assisted environmental monitoring project that explores how satellite-derived vegetation data and historical observations can help us understand changing landscapes.

The project combines satellite data retrieval, historical vegetation analysis, a Flask-based dashboard, and a Large Language Model (LLM) explanation endpoint. Its long-term objective is to support regional vegetation monitoring and investigate how historical environmental patterns can inform future vegetation trend estimation.

Rather than treating satellite observations as isolated snapshots, TerraWatch AI is designed around the idea that vegetation should be studied across geographical regions and over time.

1. Project Overview

Vegetation conditions vary with seasons, rainfall, temperature, irrigation, land-use changes, and other environmental factors. Understanding these changes requires historical observations, appropriate analysis methods, and careful interpretation.

TerraWatch AI explores a data-driven workflow for answering three questions:

Historical Analysis: What vegetation patterns have been observed in a selected region?
Change Monitoring: How have vegetation indicators changed across different observation periods?
Future Research: How can historical observations be used to investigate potential future vegetation trends?

The current project includes a local Flask application, a single-file HTML/CSS/JavaScript dashboard, result CSV loading, and an OpenRouter-powered explanation endpoint. It also includes a script for requesting historical satellite-derived NDVI data through NASA AppEEARS.

Current implementation note: The dashboard and explanation API form the application foundation. The starter does not automatically load trained forecasting models or generate future predictions until the actual model-loading and inference code is integrated.

2. Core Objectives
Retrieve historical satellite-derived vegetation observations.
Analyze vegetation indicators across geographical regions and observation periods.
Organize historical data for further environmental analysis.
Display processed results through an interactive dashboard.
Provide AI-assisted explanations of available data and screening signals.
Establish a foundation for future machine learning and time-series forecasting.
Explore the potential of combining remote sensing and AI for environmental monitoring.
3. How TerraWatch AI Works

The intended workflow connects satellite observations with historical analysis and an accessible user interface.

              Geographic Region
                      |
                      v
           Historical Satellite Data
                      |
                      v
             NASA AppEEARS API
                      |
                      v
          Satellite-Derived NDVI Data
                      |
                      v
           Data Cleaning and Validation
                      |
                      v
            Historical Data Analysis
                      |
                      v
           Processed Results in CSV
                      |
                      v
             Flask Backend
                      |
             +--------+--------+
             |                 |
             v                 v
      Web Dashboard       OpenRouter LLM
             |                 |
             +--------+--------+
                      |
                      v
            Data Visualization and
              AI-Assisted Insights
                      |
                      v
           Future Model Integration

The workflow distinguishes historical data retrieval, application-level analysis, and future predictive modeling. Each stage requires its own implementation and validation.

4. Satellite Data and Vegetation Monitoring
NASA AppEEARS

TerraWatch AI includes a Python script for requesting satellite-derived vegetation observations using NASA's Application for Extracting and Exploring Analysis Ready Samples (AppEEARS).

Official resource: NASA AppEEARS

The configured satellite data product is:

Property	Details
Data platform	NASA Earth observation data services
Retrieval service	NASA AppEEARS
Satellite product	MODIS MOD13Q1 Version 6.1
Vegetation indicator	Normalized Difference Vegetation Index (NDVI)
Spatial resolution	250 m
Temporal compositing interval	16 days
Output format	CSV

The MODIS MOD13Q1 product provides vegetation-index observations at a nominal spatial resolution of 250 metres and a 16-day compositing interval.

Understanding NDVI

The Normalized Difference Vegetation Index (NDVI) is derived from near-infrared and red reflectance:

[
NDVI = \frac{NIR - Red}{NIR + Red}
]

NDVI is commonly used to characterize vegetation greenness and monitor changes in vegetation activity.

Historical NDVI observations can help researchers investigate:

Seasonal vegetation patterns.
Changes in vegetation greenness.
Unusual variations in vegetation indicators.
Differences between observation periods.
Long-term regional vegetation trends.

NDVI is an indicator, not a complete ecological diagnosis. It does not independently identify plant species, establish the cause of vegetation stress, or guarantee a specific future outcome.

Historical Data Retrieval

The nasa_appeears.py script:

Reads geographical coordinates from an existing results CSV.
Requests historical MODIS NDVI observations through NASA AppEEARS.
Uses NASA Earthdata authentication.
Submits a satellite-data request for the configured observation period.
Downloads available results in CSV format.

The script supports historical data retrieval; it does not independently train a forecasting model or generate future vegetation predictions.

5. Regional Analysis and Future Prediction

One of TerraWatch AI's long-term goals is to investigate how historical vegetation observations can support estimates of future vegetation conditions in a selected region.

A scientifically meaningful forecasting workflow would require:

Historical observations covering an appropriate time period.
Data quality checks and preprocessing.
A clearly defined prediction target.
A trained and validated forecasting model.
Evaluation on observations excluded from training.
Appropriate uncertainty estimates and limitations.

For example, a future implementation could estimate a vegetation indicator for a particular region and future period using historical observations and relevant environmental variables.

However, predicting a vegetation indicator is different from identifying which plant species will grow in an area. Species-level predictions would require additional ecological data and suitable validated models.

Current status: Future vegetation forecasting is a development objective, not a claim that the current starter application already performs automated forecasting.

6. Technology Stack
Component	Technology
Programming language	Python
Backend framework	Flask
Frontend	HTML, CSS, JavaScript
Satellite data retrieval	NASA AppEEARS API
Satellite data product	MODIS MOD13Q1.061
Vegetation indicator	NDVI
Tabular data handling	Pandas
HTTP requests	Requests
LLM integration	OpenRouter API
Default LLM	openai/gpt-4o-mini
Data exchange	CSV and JSON
Local development	VS Code
7. Project Structure
TerraWatch_AI_VSCode/
│
├── app.py
│
├── nasa_appeears.py
│
├── data/
│   └── ndvi_input_template.csv
│
├── models/
│   ├── README.md
│   └── anomaly_model.py
│
├── outputs/
│   ├── README.md
│   ├── terrawatch_historical_backtest.csv
│   ├── terrawatch_model_report.json
│   └── terrawatch_rajasthan_results_completed.csv
│
├── templates/
│   └── index.html
│
├── requirements.txt
│
└── README.md
Main Components
app.py

Runs the local Flask backend and provides API endpoints for application status, result summaries, CSV previews, and AI-assisted explanations.

nasa_appeears.py

Implements the satellite-data retrieval workflow using NASA AppEEARS. It uses coordinates from an existing results CSV to request historical MODIS NDVI observations.

data/

Contains the input template used to prepare or organize data for the project.

models/

Contains model-related code and documentation. The starter does not automatically load trained model artifacts or execute model inference unless the relevant integration is implemented.

outputs/

Contains result CSV files and a model report. These files support result inspection and provide a basis for further evaluation and development.

templates/index.html

Contains the web dashboard interface implemented using HTML, CSS, and JavaScript.

requirements.txt

Lists the Python dependencies required by the application.

8. Installation and Setup
Prerequisites
Python 3.10 or later recommended.
Visual Studio Code.
Git.
Internet access for external API requests.
NASA Earthdata credentials for satellite-data retrieval.
An OpenRouter API key for the LLM explanation endpoint.
Step 1: Clone the Repository
git clone https://github.com/priyanshukumarverma091-hub/TerraWatch_AI_VSCode.git

Move into the project directory:

cd TerraWatch_AI_VSCode
Step 2: Create a Virtual Environment

On Windows:

python -m venv .venv

Activate the environment:

.venv\Scripts\activate
Step 3: Install Dependencies
pip install -r requirements.txt
Step 4: Configure the OpenRouter API Key

The current local starter uses a placeholder in app.py:

OPENROUTER_API_KEY = "PASTE_YOUR_OPENROUTER_API_KEY_HERE"

For local testing, replace the placeholder with a valid OpenRouter API key.

The current implementation intentionally uses a source-code configuration rather than a .env file.

Security warning: Never commit app.py with a real API key to a public GitHub repository. Before publishing, verify that the placeholder is still present and that no real credentials appear in Git history.

If a key is exposed, revoke it and create a replacement.

The default model is:

OPENROUTER_MODEL = "openai/gpt-4o-mini"

Use a model identifier supported by your OpenRouter account if you change this setting.

Step 5: Run the Application
python app.py

Open the dashboard in your browser:

http://127.0.0.1:5000

This address is for local development on your own computer.

9. Retrieving Historical NDVI Data

The satellite-data retrieval script can be run with:

python nasa_appeears.py

The script prompts for NASA Earthdata credentials and the observation period.

The default historical period configured in the starter is:

Start date: 1 January 2015.
End date: 31 December 2021.

The script reads an existing results CSV to obtain geographical coordinates and requests data for up to 100 unique coordinate locations.

Available results are downloaded as CSV files into the outputs/ directory.

Important Requirements
A suitable input CSV must exist.
The CSV must contain the coordinate fields expected by the script.
NASA Earthdata authentication must succeed.
The requested product and observation period must be available.
The AppEEARS request must complete successfully.

Actual results depend on the input coordinates, product availability, and API response.

10. Dashboard and API Endpoints

The Flask backend exposes the following endpoints:

Method	Endpoint	Purpose
GET	/api/status	Checks backend and API-key status
GET	/api/summary	Returns a brief summary of available results
GET	/api/results	Returns a preview of the latest results CSV
POST	/api/explain	Requests an AI-assisted explanation through OpenRouter
Result Preview

The dashboard loads the latest available CSV and previews up to 30 rows.

The LLM explanation endpoint can receive a user's question and structured context about the available results. When results are loaded, the context includes information such as:

CSV filename.
Column names.
Row count.
Preview of up to 30 rows.

This enables the LLM to provide explanations grounded in the data supplied to it.

The quality of the response depends on the supplied context, the underlying data, and the selected language model.

11. LLM Explanation and Responsible Interpretation

TerraWatch AI uses OpenRouter to connect the application to a language model for explaining available data.

The /api/explain endpoint is intended to help users interpret screening signals and understand the contents of the loaded results.

The LLM is instructed not to diagnose crop disease or infer a definitive cause from NDVI alone.

AI-generated responses are supplementary explanations. They are not independently verified scientific findings, agricultural diagnoses, or guaranteed predictions.

For important environmental or agricultural decisions, interpretations should be checked against the underlying observations and appropriate domain expertise.

12. Model Integration

The starter application intentionally leaves trained model artifacts out of the repository.

To connect an actual model:

Place the required model artifacts in models/.
Implement the appropriate model-loading logic.
Prepare input features using the same preprocessing used during training.
Add an inference function to the application or a dedicated model module.
Define how predictions are returned and displayed.
Validate the model using held-out observations.
Document the model's training data, evaluation metrics, and limitations.

If the model generates regional predictions, those outputs can be saved in a CSV file under outputs/ for the dashboard to load.

The starter does not automatically run inference merely because a model file is present.

Refer to models/README.md and the integration markers in app.py for project-specific guidance.

13. Evaluation and Validation

Environmental prediction systems should be evaluated using appropriate validation procedures.

Potential evaluation practices include:

Temporal separation of training, validation, and test observations.
Prevention of data leakage between historical and evaluation periods.
Comparison of model estimates with actual observations.
Comparison against simple seasonal or historical baselines.
Reporting suitable metrics for the prediction task.
Documentation of missing data, coverage, and uncertainty.

Historical backtesting is useful for evaluating model performance on previously unseen periods. However, historical performance does not guarantee future accuracy.

Metrics reported in existing project outputs should be interpreted according to the corresponding model, dataset, target variable, and evaluation procedure.

14. Limitations

TerraWatch AI is an evolving research and development project.

Important limitations include:

The local starter does not automatically execute a trained forecasting model.
Historical satellite-data retrieval and future prediction are separate processes.
NDVI measures vegetation greenness and cannot independently identify plant species.
Satellite observations may be affected by clouds, atmospheric conditions, missing observations, and measurement limitations.
Vegetation changes may be influenced by rainfall, temperature, irrigation, soil conditions, land management, and other factors.
Historical patterns may not continue under future environmental conditions.
LLM explanations may be incomplete or incorrect.
Public deployment requires additional security, configuration, and operational safeguards.

The project should be treated as an environmental monitoring and research tool, not a replacement for field surveys, ecological assessment, or expert agricultural advice.

15. Future Development

Potential development directions include:

Interactive selection of geographical regions.
Automated satellite-data retrieval and preprocessing.
Time-series forecasting of vegetation indicators.
Improved anomaly detection and historical change analysis.
Integration of rainfall and temperature observations.
Spatial visualization of regional vegetation patterns.
Prediction uncertainty estimation.
More rigorous temporal backtesting.
Automated environmental reports.
Reproducible model training and inference pipelines.

These are proposed improvements; their implementation status should be updated as the project evolves.

16. Project Vision

TerraWatch AI explores a practical intersection of remote sensing, environmental data analysis, and artificial intelligence.

The broader vision is to investigate how historical satellite observations and machine learning can help us better understand changing landscapes and support more informed environmental monitoring.

By connecting regional data with accessible analysis tools, TerraWatch AI aims to establish a foundation for future research into vegetation trends and environmental change.

17. Author

Priyanshu Kumar Verma

B.Tech Computer Science and Engineering

Areas of interest:

Artificial Intelligence and Machine Learning
Remote Sensing and Geospatial Analysis
Environmental AI
Data-Driven Research

GitHub: priyanshukumarverma091-hub

Project repository: TerraWatch AI

18. License

A license has not yet been specified for this repository.

Choose and add an appropriate license before allowing others to reuse, modify, or redistribute the project.

TerraWatch AI — Exploring vegetation change through satellite observations, historical data, and artificial intelligence.
