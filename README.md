# Log Analyzer

This script allows to analyze nginx web server logs and reports calculations and time measurements for each url accessed

--------


## Usage

run the log analyzer
```bash
python log_analyzer.py
```


run the log analyzer with the json configuration file
```bash
python log_analyzer.py --config /path/to/config.json
```


run tests
```bash
python -m unittest
```

## Assumptions

Expected log file filename formats
Files can be of plain text or .gz, .gzip,  for example:

* nginx-access-ui.log-20170630
* nginx-access-ui.log-20170630.gz
* nginx-access-ui.log-20170630.gzip


The script result will be inserted to the report directory:
* report-2017.06.30.html


User can provide json configuration file with the log directory, report directory and report size:
```
{
    "REPORT_SIZE": 800,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log"
}
```
