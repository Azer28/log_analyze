#!/usr/bin/env python
# -*- coding: utf-8 -*-


# log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$F" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';
from argparse import ArgumentParser
from datetime import datetime
from decimal import Decimal
import json
import os
from pathlib import Path
import re
from collections import defaultdict
from statistics import median
import gzip
from typing import Dict, List, Tuple
import logging
from string import Template


logging.basicConfig(
    filename='log_processor_logs.log',
    format='[%(asctime)s] %(levelname).1s %(message)s', 
    datefmt='%Y.%m.%d %H:%M:%S',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log"
}


DEFAULT_CONFIG_PATH = "config.json"


def main():
    final_config = generate_config()
    log_file_name, file_ext = find_log_file(final_config["LOG_DIR"])
    report_file_name = build_report_file_name(log_file_name)
    
    if Path(f"{final_config['REPORT_DIR']}/{report_file_name}").exists():
        logger.warning('Log analyzer has been executed already. Check the file %s', report_file_name)
    else:
        abs_filepath = f"{final_config['LOG_DIR']}/{log_file_name}"
        read_gen = readlines_gzip if file_ext in [".gz", ".gzip"] else readlines
        table = generate_table_json(abs_filepath, read_generator=read_gen)
        if table:
            create_report(rows=table, report_name=report_file_name, config=final_config)


def generate_config() -> dict:
    arg_parser = ArgumentParser()
    arg_parser.add_argument("--config", type=str, default=DEFAULT_CONFIG_PATH)
    args = arg_parser.parse_args()
    
    config_path = Path(args.config)
    if config_path.exists():
        with open(config_path) as conf_file:
            config_from_file = json.load(conf_file)
            final_config = {**config, **config_from_file} # merge two configs
            return final_config
    else:
        raise ValueError(f"Config file does not exist {config_path}")


def build_report_file_name(log_file_name: str) -> str:
    find_date_part = re.findall("nginx-access-ui.log-(\d{8})(?:.gzip|.gz)?$", log_file_name)
    date_part = find_date_part[0]
    dt = datetime.strptime(date_part, "%Y%m%d")
    return f"report-{dt.strftime('%Y')}.{dt.strftime('%m')}.{dt.strftime('%d')}.html"


def generate_table_json(abs_filename: str, read_generator) -> List[Dict]:
    logged_urls = defaultdict(list)
    sum_req_time = 0
    parse_error = 0
    i = 1 

    for i, x in enumerate(read_generator(abs_filename), start=1):
        try:
            # regex with first non-capturing group and non-greedy search
            res = re.findall('(?:GET|POST|HEAD|PUT|OPTIONS)\s(.*?)\sHTTP', x)
            if res:
                endpoint = res[0]
                req_time = re.findall("\s(\d+\.\d+)$", x)[0]
                req_time_decimal = Decimal(req_time)
                logged_urls[endpoint].append(req_time_decimal)
                sum_req_time += Decimal(req_time)
            else:
                parse_error += 1
        except Exception as exc:
            logger.exception("Error on processing %s-th line- %s", i, x)
            parse_error += 1

    if parse_error/i*100 > 50:
        logger.warning('Number of rows with incorrect format is more than 50 percent. Logfile %s', abs_filename)
        return

    table_json = [
        {
            "url": url,
            "count": len(req_times),
            "count_perc": f"{len(req_times)/i*100:.3f}",
            "time_sum": str(sum(req_times)),
            "time_perc": f"{sum(req_times)/sum_req_time*100:.3f}",
            "time_avg": f"{sum(req_times)/len(req_times):.3f}",
            "time_max": str(max(req_times)),
            "time_med": str(median(req_times))
        }
        for url, req_times in sorted(logged_urls.items(), key=lambda item: sum(item[1]), reverse=True) # sort by the sum of the times for each request
    ]
    
    return table_json


def find_log_file(directory: str) -> Tuple[str, str]:
    file_date = 0 
    final_filename = None
    for filename in os.listdir(directory):
        search_result = re.findall("nginx-access-ui.log-(\d{8})(?:.gzip|.gz)?$", filename)
        
        if search_result:
            current_file_date = int(search_result[0])
            # find the newest file
            if current_file_date > file_date:
                file_date = int(search_result[0])
                final_filename = filename
                
    return (final_filename, Path(final_filename).suffix)


def create_report(rows: list, report_name: str, config: dict) -> None:
    report_dir = config["REPORT_DIR"]

    def read_report_template():
        with open(f"{report_dir}/report.html", "r") as f:
            report_content = f.read()
            return report_content

    template_content = read_report_template()
    template_obj = Template(template_content)
    report_content = template_obj.safe_substitute(table_json=rows[:config["REPORT_SIZE"]])
    with open(f"{report_dir}/{report_name}", "w") as f:
        f.write(report_content)
    

def readlines_gzip(name: str):
    with gzip.open(name, mode="rb") as f:
        for line in f:
            yield line.decode("utf-8")
                    
def readlines(name: str):
    with open(name, encoding="utf-8", mode="r") as f:
        for line in f:
            yield line

if __name__ == "__main__":
    main()
