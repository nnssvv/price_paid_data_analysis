# 🏠 UK Price Paid Data Analysis

This repository stores a project exploring the UK’s residential property sales using Price Paid Data from HM Land Registry. This project focuses on understanding property price trends across London boroughs and postcode districts, and builds predictive models using geographical and transactional features.

To replicate the project:

1. Download the yearly .csv files from [here](https://www.gov.uk/government/statistical-data-sets/price-paid-data-downloads) and save them under the `data` folder in the parent directory.
2. Extract the zip files with London's Shapefiles from the `assets` folder.
3. Install the dependencies listed on the `requirements.txt` file

The analysis can be replicated using the `Analysis_Notebook` Jupyter Notebook.

---

## 📁 Repository Structure

```text
price_paid_data_analysis/     # Geospatial shapefiles for London boroughs and postcode districts
├── assets/             
│   ├── boroughs_shp/    
│   └── postcodes_shp/   
├── config/                   # Configuration files or constants
├── figures/                  # Output figures from Analysis_Notebook.ipynb             
├── src/                      # Python modules and helper functions for processing and visualisation                
├── Analysis_Notebook.ipynb   # Main analysis notebook
├── requirements.txt          # Project dependencies
├── .gitignore
└── README.md
```

## 📚 Data Source
HM Land Registry’s Price Paid Data

Ordnance Survey Code-Point Open

Distributed under the Open Government Licence v3.0

## 📍 Author
Developed by Nicolas Santos ([nnssvv](https://github.com/nnssvv)).

