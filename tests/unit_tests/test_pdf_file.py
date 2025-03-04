from config.base_test import BaseTest
from services.pdf_service.pdf_service import PDFService
from utils.utils import get_testing_file_paths


class TestPdfFile(BaseTest):

    def test_pdf_file(self, master_data):
        pdf_service = PDFService()

        testing_file_paths = get_testing_file_paths()
        for testing_file in testing_file_paths:
            test_data = pdf_service.extract_data_from_pdf(testing_file, columns=2)
            pdf_service.compare_data(master_data, test_data, strict=False)
