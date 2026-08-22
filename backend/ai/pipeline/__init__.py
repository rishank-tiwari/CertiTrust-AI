"""
CertiTrust AI - Pipeline Orchestration Package.
Exports pipeline_analysis_service singleton as 'pipeline' for backward compatibility.
"""

from ai.pipeline.analysis_service import pipeline_analysis_service, PipelineAnalysisService

pipeline = pipeline_analysis_service
