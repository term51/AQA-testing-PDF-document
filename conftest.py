import os
import json
import pytest

from services.pdf_service.pdf_service import PDFService


@pytest.fixture(scope="session")
def master_data(tmp_path_factory):
    project_root = os.path.dirname(__file__)
    fixtures_path = os.path.join(project_root, "fixtures")
    master_pdf_file_path = os.path.join(fixtures_path, "master.pdf")
    master_json_file_path = os.path.join(fixtures_path, "master_data.json")

    pdf_service = PDFService()
    data = pdf_service.extract_data_from_pdf(master_pdf_file_path, columns=2)

    try:
        with open(master_json_file_path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Error saving file: {e}")

    return data
