import math
import pymupdf
import pdf2image
from pyzbar.pyzbar import decode


class PDFService:
    def __init__(
            self,
            dpi=72,
            tolerance=5,
            poppler_path="D:\\work-programs\\poppler-24.08.0\\Library\\bin",
    ):
        self._strict = False
        self._pdf_path = None
        self._dpi = dpi
        self._tolerance = tolerance
        self._poppler_path = poppler_path
        self._last_key = None
        self._extracted_data = {}
        self._page_width = None
        self._columns = None
        self._errors = []

    def extract_data_from_pdf(self, pdf_path, columns=1):
        self._columns = columns
        self._pdf_path = pdf_path
        doc = pymupdf.open(pdf_path)

        for page_num, page in enumerate(doc):
            text_data = page.get_text("dict")
            draws = page.get_drawings()
            self._page_width = round(text_data["width"])
            self._extracted_data[f"page_{page_num}"] = {
                "titles": [],
                "text_data": {},
                "rectangles": [],
                "barcodes": []
            }

            self.__add_rectangles(page_num, draws)

            for block in text_data.get("blocks", []):
                lines = block.get("lines", [])
                for line in lines:
                    spans = line.get("spans", [])
                    for span in spans:
                        text = span.get("text").strip()

                        if not text:
                            continue

                        if span.get("size") > 10:
                            self.__add_title(page_num, span)
                        else:
                            self.__add_text(page_num, span)

        self.__add_barcodes()
        return self._extracted_data

    def compare_data(self, master_data, test_data, strict=False):
        self._strict = strict
        for master_page_key, master_page_data in master_data.items():
            assert len(master_data.items()) == len(test_data.items()), "Number of pages doesn't match"

            test_page_data = test_data.get(master_page_key, {})
            self.__compare_titles(master_page_data["titles"], test_page_data["titles"])
            self.__compare_text_data(master_page_data["text_data"], test_page_data["text_data"])
            self.__compare_barcodes(master_page_data["barcodes"], test_page_data["barcodes"])

        if self._errors:
            print('errors  ', self._errors)
            self._errors = []

    def __extend_bbox(self, bbox, full=False):
        if self._page_width:
            width = self._page_width if full else math.floor(self._page_width / self._columns)
        else:
            raise ValueError("Page width is not defined")

        try:
            x1, y1, x2, y2 = bbox
        except ValueError:
            raise ValueError("bbox must contain exactly 4 values")

        x2 = width
        while x2 < x1:
            x2 += width

        return x1, y1, x2, y2

    def __add_title(self, page_num, span):
        extended_bbox = self.__extend_bbox(span.get("bbox"), full=True)
        span["bbox"] = extended_bbox
        self._extracted_data[f"page_{page_num}"]["titles"].append(
            self.__get_text_data(span.get("text").strip(), span)
        )

    def __add_text(self, page_num, span):
        text = span.get("text").strip()

        if self._last_key and self.__is_text_inside_rectangle(page_num, span):
            self.__add_text_to_rectangle(page_num, span)

        elif ':' in text:
            key, value = text.split(":", 1)
            key = key.strip()

            split_index = text.index(":")
            key_text = text[:split_index + 1]
            value_text = text[split_index + 1:]

            self._last_key = key

            key_data = self.__get_text_data(key_text, span)

            extended_bbox = self.__extend_bbox(span.get("bbox"))
            span["bbox"] = extended_bbox
            value_data = self.__get_text_data(value_text, span)

            self._extracted_data[f"page_{page_num}"]["text_data"][key] = {
                "key_data": key_data,
                "value_data": value_data if value_data["text"] else None
            }

        elif self._last_key:
            extended_bbox = self.__extend_bbox(span.get("bbox"))
            span["bbox"] = extended_bbox
            value_data = self.__get_text_data(text, span)
            self._extracted_data[f"page_{page_num}"]["text_data"][self._last_key]["value_data"] = value_data
            self._last_key = None

        else:
            self._last_key = text
            key_data = self.__get_text_data(text, span)
            self._extracted_data[f"page_{page_num}"]["text_data"][text] = {
                "key_data": key_data,
                "value_data": None
            }

    def __add_rectangles(self, page_num, draws):
        for item in draws:
            if 'rect' in item and any(op[0] == 're' for op in item['items']):
                rect = item['rect']
                coords = (math.ceil(rect.x0), math.ceil(rect.y0), math.floor(rect.x1), math.floor(rect.y1))
                if any(coord == 0 for coord in coords):
                    continue
                self._extracted_data[f"page_{page_num}"]["rectangles"].append({
                    "text": "",
                    "bbox": coords
                })

    def __get_text_data(self, text, span):
        return {
            "text": text,
            "size": round(span.get("size"), 1),
            "font": span.get("font"),
            "color": span.get("color"),
            "alpha": span.get("alpha"),
            "bbox": tuple(math.floor(p) for p in span.get("bbox", []))
        }

    def __is_text_inside_rectangle(self, page_num, span):
        x1, y1, x2, y2 = span.get("bbox")
        for rect in self._extracted_data[f"page_{page_num}"]["rectangles"]:
            rx1, ry1, rx2, ry2 = rect.get("bbox")
            if rx1 <= x1 and ry1 <= y1 and rx2 >= x2 and ry2 >= y2:
                return True
        return False

    def __add_text_to_rectangle(self, page_num, span):
        x1, y1, x2, y2 = span.get("bbox")
        text = span.get("text").strip()
        for rect in self._extracted_data[f"page_{page_num}"]["rectangles"]:
            rx1, ry1, rx2, ry2 = rect.get("bbox")
            if rx1 <= x1 and ry1 <= y1 and rx2 >= x2 and ry2 >= y2:
                rect["text"] += text
                break

    def __add_barcodes(self):
        images = pdf2image.convert_from_path(self._pdf_path, dpi=self._dpi, poppler_path=self._poppler_path)
        for page_num, image in enumerate(images):
            barcodes = decode(image)

            for i, barcode in enumerate(barcodes):
                x, y, w, h = barcode.rect
                self._extracted_data[f"page_{page_num}"]["barcodes"].append({
                    "bbox": (x, y, x + w, y + h),
                    "text": barcode.data.decode("utf-8")
                })

    def __compare_bbox(self, bbox1, bbox2):
        if self._strict:
            return bbox1 == bbox2

        if len(bbox1) != len(bbox2):
            return False

        return all(abs(b1 - b2) <= self._tolerance for b1, b2 in zip(bbox1, bbox2))

    def __compare_titles(self, master_titles, test_titles):
        assert len(master_titles) == len(test_titles), "Number of titles doesn't match"

        for i, master_title in enumerate(master_titles):
            assert self.__compare_bbox(
                master_title["bbox"],
                test_titles[i]["bbox"]
            ), f"The title '{test_titles[i]['text']}' is out of place"

    def __compare_text_data(self, master_text_data, test_text_data):
        for master_key, master_data in master_text_data.items():
            test_data = test_text_data.get(master_key)
            assert test_data, f"Missing '{master_key}' key"

            if master_data["key_data"]:
                assert master_data["key_data"]["text"] == test_data["key_data"]["text"], \
                    f"The text '{test_data["key_data"]["text"]}' of {master_key} is different"
                assert master_data["key_data"]["size"] == test_data["key_data"]["size"], \
                    f"The size '{test_data["key_data"]["size"]}' of {master_key} is different"
                assert master_data["key_data"]["font"] == test_data["key_data"]["font"], \
                    f"The font '{test_data["key_data"]["font"]}' of {master_key} is different"
                assert master_data["key_data"]["color"] == test_data["key_data"]["color"], \
                    f"The color '{test_data["key_data"]["color"]}' of {master_key} is different"
                assert master_data["key_data"]["alpha"] == test_data["key_data"]["alpha"], \
                    f"The alpha '{test_data["key_data"]["alpha"]}' of {master_key} is different"
                assert self.__compare_bbox(
                    master_data["key_data"]["bbox"],
                    test_data["key_data"]["bbox"]
                ), f"The bbox '{test_data["key_data"]['text']}' is out of place"

            if master_data["value_data"]:
                assert master_data["value_data"]["size"] == test_data["value_data"]["size"], \
                    f"The size '{test_data["key_data"]["size"]}' of {master_key} is different"
                assert master_data["value_data"]["font"] == test_data["value_data"]["font"], \
                    f"The font '{test_data["key_data"]["font"]}' of {master_key} is different"
                assert master_data["value_data"]["color"] == test_data["value_data"]["color"], \
                    f"The color '{test_data["key_data"]["color"]}' of {master_key} is different"
                assert master_data["value_data"]["alpha"] == test_data["value_data"]["alpha"], \
                    f"The alpha '{test_data["key_data"]["alpha"]}' of {master_key} is different"
                assert self.__compare_bbox(
                    master_data["value_data"]["bbox"],
                    test_data["value_data"]["bbox"]
                ), f"The bbox '{test_data["value_data"]['text']}' is out of place"

    def __compare_barcodes(self, master_barcodes, test_barcodes):
        assert len(master_barcodes) == len(test_barcodes), "Number of barcodes doesn't match"

        for i, master_barcode in enumerate(master_barcodes):
            test_barcode = test_barcodes[i]
            assert master_barcode["text"] == test_barcode["text"], f"Barcode '{test_barcode['text']}' doesn't match"
            assert self.__compare_bbox(master_barcode["bbox"], test_barcode["bbox"]), \
                f"[Barcode '{test_barcode['text']}' is out of place"
