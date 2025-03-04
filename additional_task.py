import re
import json

table = [
    {
        'Columns View': 'SO Number',
        'Sort By': '',
        'Highlight By': 'equals=S110=rgba(172,86,86,1),equals=S111',
        'Condition': 'equals=S110,equals=S111',
        'Row Height': '60',
        'Lines per page': '25'
    },
    {
        'Columns View': 'Client PO',
        'Sort By': '',
        'Highlight By': 'equals=P110,equals=P111',
        'Condition': 'equals=P110',
        'Row Height': '', 'Lines per page': ''
    },
    {
        'Columns View': 'Terms of Sale',
        'Sort By': 'asc',
        'Highlight By': 'equals=S110=rgba(172,86,86,1)',
        'Condition': '',
        'Row Height': '',
        'Lines per page': ''
    }
]

# base_ws = {
#     'Columns View': 'columns',
#     'Sort By': 'order_by',
#     'Condition': 'conditions_data',
#     'Lines per page': 'page_size',
#     'Row Height': 'row_height',
#     'Highlight By': 'color_conditions'
# }

websocket_response = {
    'Client PO': {'index': 'so_list_client_po', 'filter': 'client_po'},
    'SO Number': {'index': 'so_list_so_number', 'filter': 'so_no'},
    'Terms of Sale': {'index': 'so_list_terms_of_sale', 'filter': 'term_sale'}
}


#
# result = {
#     'columns': [
#         {'index': 'so_list_so_number', 'sort': 0},
#         {'index': 'so_list_client_po', 'sort': 1},
#         {'index': 'so_list_terms_of_sale', 'sort': 2}
#     ],
#     'order_by': {
#         'direction': 'asc',
#         'index': 'so_list_terms_of_sale'
#     },
#     'conditions_data': {
#         'so_no': [
#             {'type': 'equals', 'value': 'S110'},
#             {'type': 'equals', 'value': 'S111'}
#         ],
#         'client_po': [
#             {'type': 'equals', 'value': 'P110'}
#         ]
#     },
#     'page_size': '25',
#     'row_height': '60',
#     'color_conditions': {
#         'so_no': [
#             {
#                 'type': 'equals',
#                 'value': 'S110',
#                 'color': 'rgba(172,86,86,1)'
#             }
#         ],
#         'client_po': [
#             {'type': 'equals', 'value': 'S110', 'color': ''},
#             {'type': 'equals', 'value': 'S111', 'color': ''}
#         ],
#         'term_sale': []
#     },
#     'module': 'SO'
# }


class TableConverter:
    def __init__(self, table, websocket_response):

        if not isinstance(table, list) or any(not isinstance(row, dict) for row in table):
            raise TypeError("Error: table must be a list of dicts")

        if not isinstance(websocket_response, dict):
            raise TypeError("Error: websocket_response must be a dict")

        self.result = {"module": "SO"}
        self.table = table
        self.websocket_response = websocket_response
        self.base_ws = {
            'Columns View': 'columns',
            'Sort By': 'order_by',
            'Condition': 'conditions_data',
            'Lines per page': 'page_size',
            'Row Height': 'row_height',
            'Highlight By': 'color_conditions'
        }
        self.sort = 0

        for row in self.table:
            self.condition_filter_key = self.websocket_response.get(row["Columns View"], {}).get("filter")
            self.__process_row(row)

    def __process_row(self, row):
        for col in row:
            base_ws_value = self.base_ws.get(col)
            if base_ws_value is None:
                continue

            self.__process_column(row, col)

    def __process_column(self, row, col):
        column_value = row.get(col, "")

        if column_value in self.websocket_response:
            self.__add_column(column_value)

        if "Lines per page" == col and column_value:
            self.result["page_size"] = row["Lines per page"]

        if "Row Height" == col and column_value:
            self.result["row_height"] = row["Row Height"]

        if "Sort By" == col and column_value:
            self.__add_sorting(row)

        if "Condition" == col and column_value and self.condition_filter_key:
            self.__add_conditions(row)

        if "Highlight By" == col and column_value and self.condition_filter_key:
            self.__add_highlight(row)

    def __add_column(self, col_name):
        key = "index"
        if "columns" not in self.result:
            self.result["columns"] = []

        self.result["columns"].append(
            {key: self.websocket_response[col_name][key], 'sort': self.sort}
        )
        self.sort += 1

    def __add_sorting(self, row):
        self.result["order_by"] = {
            "direction": row["Sort By"],
            "index": self.websocket_response.get(row["Columns View"], {}).get("index", "")
        }

    def __get_conditions(self, condition):
        condition_type = condition_value = condition_color = ""
        if "=" in condition:
            parts = condition.split("=")
            condition_type = parts[0] if len(parts) > 0 else ""
            condition_value = parts[1] if len(parts) > 1 else ""
            condition_color = parts[2] if len(parts) > 2 else ""

        return condition_type, condition_value, condition_color

    def __add_conditions(self, row):
        conditions = []
        matches = self.__parse_conditions(row["Condition"])
        for match in matches:
            condition = match.group(0)
            condition_type, condition_value, _ = self.__get_conditions(condition)
            conditions.append({"type": condition_type, "value": condition_value})

        if "conditions_data" not in self.result:
            self.result["conditions_data"] = {}

        self.result["conditions_data"][self.condition_filter_key] = conditions

    def __add_highlight(self, row):
        conditions = []
        matches = self.__parse_conditions(row["Highlight By"])
        for match in matches:
            condition = match.group(0)
            condition_type, condition_value, condition_color = self.__get_conditions(condition)
            conditions.append({"type": condition_type, "value": condition_value, "color": condition_color})

        if "color_conditions" not in self.result:
            self.result["color_conditions"] = {}

        self.result["color_conditions"][self.condition_filter_key] = conditions

    def __parse_conditions(self, string):
        pattern = r"(equals)=(\w\d+)(?:=.*?(rgba\(\d+,\d+,\d+,\d+(?:\.\d+)?\)))?"
        return re.finditer(pattern, string)

    def __str__(self):
        return self.result.__str__()

    def to_json(self):
        return json.dumps(self.result, indent=4)


print(TableConverter(table, websocket_response).to_json())
