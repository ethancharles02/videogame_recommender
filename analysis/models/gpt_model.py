from openai import OpenAI
from .analysis_model import AnalysisModel

class GptAnalyisModel(AnalysisModel):
    def __init__(self):
        super().__init__()
        self.model_type = "gpt-5-mini"

    def setup(self):
        self.client = OpenAI()

    def send_query(self, query: str):
        response = self.client.responses.create(model=self.model_type, input=query)
        return response.output_text