"""
CertiTrust AI - Master AI Processing Pipeline Orchestrator.
Connects image preprocessing, OCR, entity extraction, CV analysis, metadata inspection,
fraud detection, trust scoring, and audit report generation.
"""

import hashlib
from typing import Dict, Any
from ai.preprocessing.image_processor import ImagePreprocessor
from ai.ocr.engine import OCREngine
from ai.extraction.entity_extractor import EntityExtractor
from ai.cv_analysis.stamp_detector import StampDetector
from ai.metadata.pdf_inspector import PDFMetadataInspector
from ai.fraud_detection.tamper_detector import FraudTamperDetector
from ai.scoring.trust_engine import TrustScoringEngine
from ai.reports.audit_generator import AuditReportGenerator
from app.utils.logger import logger


class CertiTrustAIPipeline:
    """
    End-to-end AI document analysis and fraud verification pipeline.
    """

    def __init__(self):
        self.preprocessor = ImagePreprocessor()
        self.ocr_engine = OCREngine()
        self.entity_extractor = EntityExtractor()
        self.stamp_detector = StampDetector()
        self.metadata_inspector = PDFMetadataInspector()
        self.tamper_detector = FraudTamperDetector()
        self.scoring_engine = TrustScoringEngine()
        self.report_generator = AuditReportGenerator()

    def process_document(self, document_id: str, filename: str, file_bytes: bytes) -> Dict[str, Any]:
        """
        Runs document through all 8 stages of the AI pipeline.

        Returns:
            Dict[str, Any]: Complete audit report with trust score, extracted entities, and fraud flags.
        """
        logger.info(f"Starting CertiTrust AI Pipeline for Document ID: {document_id} ({filename})")

        # 0. Calculate SHA-256 Cryptographic Hash for Blockchain Verification
        doc_hash = hashlib.sha256(file_bytes).hexdigest()

        # 1. Preprocessing Stage
        processed_bytes, prep_metadata = self.preprocessor.preprocess_image(file_bytes)

        # 2. OCR Stage
        ocr_result = self.ocr_engine.extract_text(processed_bytes, filename)

        # 3. Entity Extraction Stage
        entities = self.entity_extractor.extract_entities(ocr_result["full_text"])

        # 4. Computer Vision Feature Analysis Stage
        cv_result = self.stamp_detector.analyze_visual_features(processed_bytes, filename)

        # 5. Metadata Inspection Stage
        metadata_result = self.metadata_inspector.inspect_metadata(file_bytes, filename)

        # 6. Fraud & Tampering Detection Stage
        fraud_result = self.tamper_detector.analyze_tampering(file_bytes, ocr_result, metadata_result)

        # 7. Authenticity & Trust Scoring Stage
        scoring_result = self.scoring_engine.compute_trust_score(
            ocr_result=ocr_result,
            cv_result=cv_result,
            metadata_result=metadata_result,
            fraud_result=fraud_result,
        )

        # 8. Audit Report Generation Stage
        final_report = self.report_generator.generate_report(
            document_id=document_id,
            filename=filename,
            document_hash=doc_hash,
            entities=entities,
            scoring_result=scoring_result,
            fraud_result=fraud_result,
            metadata_result=metadata_result,
        )

        logger.info(f"Pipeline execution finished successfully for Document ID: {document_id}")
        return final_report


# Global Singleton Pipeline Instance
pipeline = CertiTrustAIPipeline()
