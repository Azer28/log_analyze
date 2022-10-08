from pathlib import Path
import unittest

from log_analyzer import find_log_file, build_report_file_name, generate_table_json, readlines


CURRENT_DIRECTORY = Path(__file__).parent


class TestLogAnalyzer(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.test_dir = "test_data"

    def test_proper_log_file_is_found(self):
        my_data_path = CURRENT_DIRECTORY / self.test_dir
        file_name, ext = find_log_file(my_data_path)
        self.assertEqual(file_name, "nginx-access-ui.log-20171030")
        self.assertNotEqual(ext, ".bz2")

    def test_report_name(self):
        res = build_report_file_name(log_file_name="nginx-access-ui.log-20191230.gz")
        self.assertEqual(res, "report-2019.12.30.html")

    def test_file_parse(self):
        res_table = generate_table_json(CURRENT_DIRECTORY / self.test_dir/ "nginx-access-ui.log-20171030", read_generator=readlines)
        samples_log_analytics = {
            "/api/v2/group/1769230/banners": [3, '1.479'],
            "/api/v2/group/7786679/statistic/sites/?date_type=day&date_from=2017-06-28&date_to=2017-06-28": [3, '0.193'],
            "/api/1/photogenic_banners/list/?server_name=WIN7RB4": [1, '0.133']
        }
        for generated_row in res_table:
            if generated_row["url"] in samples_log_analytics:
                current_sample_log = samples_log_analytics[generated_row["url"]]
                self.assertEqual(current_sample_log[0], generated_row["count"])
                self.assertEqual(current_sample_log[1], generated_row["time_sum"])