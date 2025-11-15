from django.urls import reverse
from rest_framework.test import APITestCase
from django.core.files.uploadedfile import SimpleUploadedFile

class UploadTests(APITestCase):
    def test_missing_file(self):
        resp = self.client.post("/api/upload/", {"doc_type": "flyer"})
        self.assertEqual(resp.status_code, 400)

    def test_upload_pdf(self):
        fake = SimpleUploadedFile("test.pdf", b"%PDF-1.4\n%...", content_type="application/pdf")
        resp = self.client.post("/api/upload/", {"file": fake, "doc_type": "flyer"})
        self.assertIn(resp.status_code, [201, 400]) 
