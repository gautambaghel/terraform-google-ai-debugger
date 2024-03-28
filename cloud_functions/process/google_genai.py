import google.auth
import vertexai
from vertexai.preview.generative_models import GenerativeModel, Part
import vertexai.preview.generative_models as generative_models

class GoogleProject:

    def __init__(self, quota_project_id=None, scopes=None):
        self.project = None
        self.quota_project_id = quota_project_id

        if scopes is None:
            self.scopes = [
                "https://www.googleapis.com/auth/cloud-platform"
            ]
        else:
            self.scopes = scopes

        credentials, default_project_id = google.auth.default(quota_project_id=self.quota_project_id,
                                                              scopes=self.scopes)
        vertexai.init(project=default_project_id, location="us-central1")
        self.model = GenerativeModel("gemini-1.0-pro-001")

    def generate_content(self, help_string: str, stream: bool = False) -> str:
        response = self.model.generate_content(
            f"""Can you help with this Terraform error, please? {help_string}""",
            generation_config={
                "max_output_tokens": 5535,
                "temperature": 0.7,
                "top_p": 1
            },
            safety_settings={
                generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            },
            stream=stream,
        )
        return f":sparkles: Terraform AI debugger (powered by Google Gemini) :sparkles: \n\n + {response.text}"

if __name__ == "__main__":
    proj = GoogleProject()
    proj.generate_content("I need help with my terraform code", stream=False)
